/**
 * Copyright 2018, Radiant Solutions, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi.services;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

import javax.annotation.PostConstruct;

import org.geotools.feature.FeatureCollection;
import org.geotools.feature.FeatureIterator;
import org.geotools.geojson.feature.FeatureJSON;
import org.joda.time.DateTime;
import org.joda.time.Duration;
import org.joda.time.Hours;
import org.joda.time.Minutes;
import org.opengis.feature.simple.SimpleFeature;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;

import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryCollection;
import com.vividsolutions.jts.geom.GeometryFactory;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Scheduling class that manages the constant management polling for Status of Shoreline detections Jobs.
 * <p>
 * This will poll for the status of Jobs in Piazza, and update the beachfront jobs table accordingly.
 * <p>
 * Additionally, this will also track the state of Activating jobs via Planet, or other brokers.
 */
@Component
public class JobPoller {
	@Value("${piazza.poll.frequency.seconds}")
	private int POLL_FREQUENCY_SECONDS;
	@Value("${job.timeout.hours}")
	private int JOB_TIMEOUT_HOURS;
	@Value("${job.activation.timeout.minutes}")
	private int JOB_ACTIVATION_TIMEOUT_MINUTES;

	@Autowired
	private JobService jobService;
	@Autowired
	private PiazzaService piazzaService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	private PollStatusTask pollStatusTask = new PollStatusTask();
	private Timer pollTimer = new Timer();

	/**
	 * Begins scheduled polling of Beachfront Job Statuses
	 */
	@PostConstruct
	public void startPolling() {
		piazzaLogger.log("Beginning Job Management Polling.", Severity.INFORMATIONAL);
		pollTimer.schedule(pollStatusTask, 10000, POLL_FREQUENCY_SECONDS * (long) 1000);
	}

	public void stopPolling() {
		piazzaLogger.log("Cancelling Job Management Polling. Jobs will not be updated.", Severity.INFORMATIONAL);
		pollTimer.cancel();
	}

	public PollStatusTask getTask() {
		return pollStatusTask;
	}

	/**
	 * Timer Task that will, on a schedule, poll for the Status of outstanding/active Beachfront Jobs. Jobs in a
	 * non-complete state will be managed here.
	 */
	public class PollStatusTask extends TimerTask {
		@Override
		public void run() {
			try {
				// Get the list of outstanding jobs that need to be managed
				List<Job> outstandingJobs = jobService.getOutstandingJobs();
				for (Job job : outstandingJobs) {
					// If this Job is activating, it has not yet been sent to Piazza.
					if (Job.STATUS_ACTIVATING.equals(job.getStatus())) {
						// Check for timeouts. Jobs that take too long to activate will fail.
						int timeDelta = Minutes.minutesBetween(job.getCreatedOn(), new DateTime()).getMinutes();
						if (timeDelta >= JOB_ACTIVATION_TIMEOUT_MINUTES) {
							timeoutJob(job);
						}
						continue;
					}
					// For each Job currently owned by Piazza, query the status of that job in Piazza
					StatusMetadata status = null;
					try {
						status = piazzaService.getJobStatus(job.getJobId());
					} catch (UserException exception) {
						// If the Job has exceeded it's time-to-live, then mark that job a failure.
						int timeDelta = Hours.hoursBetween(job.getCreatedOn(), new DateTime()).getHours();
						if (timeDelta >= JOB_TIMEOUT_HOURS) {
							timeoutJob(job);
						}
						continue;
					}
					processJobStatus(job, status);
				}
			} catch (Exception exception) {
				piazzaLogger.log(String.format(
						"An unexpected severe error has occurred while polling for outstanding Piazza Jobs. Polling will continue, but Jobs may be negatively impacted. Inner Exception of type %s: %s",
						exception.getClass().toString(), exception.getMessage()), Severity.ERROR);
				exception.printStackTrace();
			}
		}

		/**
		 * Flags the Job as timed out. This will fail the job and update Database status accordingly.
		 * 
		 * @param job
		 *            The timed out Job
		 * @param timeDelta
		 *            For logging purposes, the amount of time that has passed before this Job failed.
		 */
		private void timeoutJob(Job job) {
			piazzaLogger.log(
					String.format("Job %s with Status %s has timed out and will be set as failure.", job.getJobId(), job.getStatus()),
					Severity.ERROR);
			// Kill the Job
			jobService.createJobError(job, "Job timed out");
			job.setStatus(Job.STATUS_ERROR);
			jobService.updateJob(job);
		}

		/**
		 * Processes the returned Piazza Job Status for the specified Beachfront Job
		 * 
		 * @param job
		 *            The Job to update
		 * @param status
		 *            The Status of the corresponding Piazza Job
		 */
		@SuppressWarnings("rawtypes")
		public void processJobStatus(Job job, StatusMetadata status) {
			// Update the Status of the Job
			job.setStatus(status.getStatus());
			if (!status.isStatusIncomplete()) {
				// Logging time of completion, and overall status at time of completion
				piazzaLogger.log(
						String.format("Job %s completed in %d minutes. Status=%s", job.getJobId(),
								new Duration(job.getCreatedOn(), new DateTime()).getStandardMinutes(), // calculate diff
																										// between now
																										// and when job
																										// was created
								job.getStatus()), // list status in message, either success or error
						Severity.INFORMATIONAL);
			}

			// Process based on the status
			if (status.isStatusIncomplete()) {
				// Nothing to do here. Polling will continue for this job.
			} else if (status.isStatusSuccess()) {
				try {
					// Download the file bytes from Piazza
					byte[] detectionBytes = piazzaService.getJobResultBytesAsGeoJson(status.getDataId(), job.getJobId());
					piazzaLogger.log(String.format("Downloaded Detection bytes, filesize %s from Piazza for Job %s", detectionBytes.length,
							job.getJobId()), Severity.INFORMATIONAL);
					// Convert the bytes into a Geometry object that Hibernate can store
					InputStream inputStream = new ByteArrayInputStream(detectionBytes);
					FeatureJSON jsonParser = new FeatureJSON();
					FeatureCollection featureCollection = jsonParser.readFeatureCollection(inputStream);
					FeatureIterator iterator = featureCollection.features();
					List<Geometry> geometries = new ArrayList<>();
					while (iterator.hasNext()) {
						SimpleFeature feature = (SimpleFeature) iterator.next();
						geometries.add((Geometry) feature.getDefaultGeometry());
					}
					Geometry[] geometryArray = new Geometry[geometries.size()];
					GeometryFactory factory = new GeometryFactory();
					GeometryCollection geometry = factory.createGeometryCollection(geometries.toArray(geometryArray));
					if (geometry == null) {
						throw new IOException("The parsed Geometry from the Shoreline is null.");
					}
					// Commit the Detection to the Detections table
					jobService.createDetection(job, geometry);
					// Finally, mark the Job as successful
					job.setStatus(Job.STATUS_SUCCESS);
					piazzaLogger.log(
							String.format("Successfully recorded Detection geometry for Job %s and marking as Success.", job.getJobId()),
							Severity.INFORMATIONAL);
					try {
						// Clean up the Piazza job if this local detection store has been successful
						piazzaService.deleteGeoJsonJobData(status.getDataId());
					} catch (Exception exception) {
						piazzaLogger.log(String.format("Couldn't clean up Piazza GeoJSON bytes for successful Job %s with Data ID %s.",
								job.getJobId(), status.getDataId()), Severity.WARNING);
					}
				} catch (IOException exception) {
					piazzaLogger.log(String.format("Job %s failed because of an internal error while reading the detection geometry.",
							job.getJobId()), Severity.ERROR);
					jobService.createJobError(job, "Invalid detection geometry error");
					job.setStatus(Job.STATUS_ERROR);
				} catch (UserException exception) {
					piazzaLogger.log(
							String.format("Job %s failed because of an internal error downloading the detection geometry.", job.getJobId()),
							Severity.ERROR);
					jobService.createJobError(job, "Unexpected detection geometry error");
					// Fail the Job as we have failed to download the bytes
					job.setStatus(Job.STATUS_ERROR);
				} catch (Exception exception) {
					piazzaLogger.log(String.format(
							"Successful Piazza Job %s failed because of an unknown internal error of type %s. Full trace will be printed to logs.",
							job.getJobId(), exception.getClass().toString()), Severity.ERROR);
					exception.printStackTrace();
					jobService.createJobError(job, "Unexpected error during processing");
					// Fail the Job as we have failed to download the bytes
					job.setStatus(Job.STATUS_ERROR);
				}
			} else if (status.isStatusError()) {
				piazzaLogger.log(String.format("Job %s reported a failure from upstream Piazza.", job.getJobId()), Severity.ERROR);
				job.setStatus(status.getStatus());
				// Attempt to get the detailed error information from the Job failure, if present.
				String errorInfo = "Unexpected error during processing"; // Default value in case none can be parsed
				if (status.getDataId() != null) {
					try {
						// Get the user-facing error message from the Algorithm's error Data
						errorInfo = piazzaService.getDataErrorInformation(status.getDataId());
					} catch (Exception exception) {
						// Log details
						String error = String.format(
								"Unable to get detailed error information for Job %s with error Data %s; encountered error: %s",
								job.getJobId(), status.getDataId(), exception.getMessage());
						exception.printStackTrace();
						piazzaLogger.log(error, Severity.ERROR);
					}
				}
				jobService.createJobError(job, errorInfo);
			}
			// Commit the updates
			jobService.updateJob(job);
		}
	}
}
