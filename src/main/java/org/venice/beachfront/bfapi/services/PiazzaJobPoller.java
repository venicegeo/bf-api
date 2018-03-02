/**
 * Copyright 2016, RadiantBlue Technologies, Inc.
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
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

import javax.annotation.PostConstruct;

import org.geotools.geojson.feature.FeatureJSON;
import org.joda.time.DateTime;
import org.joda.time.Hours;
import org.opengis.feature.simple.SimpleFeature;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;

import com.vividsolutions.jts.geom.Geometry;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Scheduling class that manages the constant polling for Status of Shoreline detections Jobs in Piazza
 */
@Component
public class PiazzaJobPoller {
	@Value("${piazza.poll.frequency.seconds}")
	private int POLL_FREQUENCY_SECONDS;
	@Value("${job.timeout.hours}")
	private int JOB_TIMEOUT_HOURS;

	@Autowired
	private JobService jobService;
	@Autowired
	private PiazzaService piazzaService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	private PollStatusTask pollStatusTask = new PollStatusTask();
	private Timer pollTimer = new Timer();

	/**
	 * Begins scheduled polling of Piazza Job Status
	 */
	@PostConstruct
	public void startPolling() {
		piazzaLogger.log("Beginning Job Polling to Piazza.", Severity.INFORMATIONAL);
		pollTimer.schedule(pollStatusTask, 10000, POLL_FREQUENCY_SECONDS * (long) 1000);
	}

	public void stopPolling() {
		piazzaLogger.log("Cancelling Job Polling to Piazza. Jobs will not be updated.", Severity.INFORMATIONAL);
		pollTimer.cancel();
	}

	/**
	 * Timer Task that will, on a schedule, poll for the Status of Piazza Jobs
	 */
	public class PollStatusTask extends TimerTask {
		@Override
		public void run() {
			// Get the list of outstanding jobs that need to be queried
			List<Job> outstandingJobs = jobService.getOutstandingJobs();
			for (Job job : outstandingJobs) {
				// For each job, query the status of that job in Piazza
				StatusMetadata status = null;
				try {
					status = piazzaService.getJobStatus(job.getJobId());
				} catch (UserException exception) {
					// If the Job has exceeded it's time-to-live, then mark that job a failure.
					int timeDelta = Hours.hoursBetween(new DateTime(), job.getCreatedOn()).getHours();
					if (timeDelta >= JOB_TIMEOUT_HOURS) {
						String error = String.format("Job % has timed out after %s hours and will be set as failure.", job.getJobId(),
								timeDelta);
						piazzaLogger.log(error, Severity.ERROR);
						// Kill the Job
						jobService.createJobError(job, error);
						job.setStatus(Job.STATUS_ERROR);
						jobService.updateJob(job);
					}
					continue;
				}
				processJobStatus(job, status);
			}
		}

		/**
		 * Processes the returned Piazza Job Status for the specified Beachfront Job
		 * 
		 * @param job
		 *            The Job to update
		 * @param status
		 *            The Status of the corresponding Piazza Job
		 */
		private void processJobStatus(Job job, StatusMetadata status) {
			// Update the Status of the Job
			job.setStatus(status.getStatus());
			// Process based on the status
			if (status.isStatusIncomplete()) {
				// Nothing to do here. Polling will continue for this job.
			} else if (status.isStatusSuccess()) {
				try {
					// Download the file bytes from Piazza
					byte[] detectionBytes = piazzaService.downloadData(status.getDataId());
					piazzaLogger.log(String.format("Downloaded Detection bytes, filesize %s from Piazza for Job %s", detectionBytes.length,
							job.getJobId()), Severity.INFORMATIONAL);
					// Convert the bytes into a Geometry object that Hibernate can store
					InputStream inputStream = new ByteArrayInputStream(detectionBytes);
					FeatureJSON featureJson = new FeatureJSON();
					SimpleFeature feature = featureJson.readFeature(inputStream);
					Geometry geometry = (Geometry) feature.getDefaultGeometry();
					// Commit the Detection to the Detections table
					jobService.createDetection(job, geometry);
					// Finally, mark the Job as successful
					job.setStatus(Job.STATUS_SUCCESS);
					piazzaLogger.log(
							String.format("Successfully recorded Detection geometry for Job %s and marking as Success.", job.getJobId()),
							Severity.INFORMATIONAL);
				} catch (IOException exception) {
					exception.printStackTrace();
					String error = String.format("Job %s failed because of an internal error while reading the detection geometry.",
							job.getJobId());
					piazzaLogger.log(error, Severity.ERROR);
					jobService.createJobError(job, error);
					job.setStatus(Job.STATUS_ERROR);
				} catch (UserException exception) {
					exception.printStackTrace();
					String error = String.format("Job %s failed because of an internal error downloading the detection geometry.",
							job.getJobId());
					piazzaLogger.log(error, Severity.ERROR);
					jobService.createJobError(job, error);
					// Fail the Job as we have failed to download the bytes
					job.setStatus(Job.STATUS_ERROR);
				}
			} else if (status.isStatusError()) {
				piazzaLogger.log(String.format("Job %s reported a failure from upstream Piazza.", job.getJobId()), Severity.ERROR);
				job.setStatus(status.getStatus());
				jobService.createJobError(job, status.getErrorMessage());
			}
			// Commit the updates
			jobService.updateJob(job);
		}
	}
}
