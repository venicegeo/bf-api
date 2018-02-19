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

import org.geotools.geojson.geom.GeometryJSON;
import org.joda.time.DateTime;
import org.joda.time.Hours;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;

import com.vividsolutions.jts.geom.Geometry;

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

	private PollStatusTask pollStatusTask = new PollStatusTask();
	private Timer pollTimer = new Timer();

	/**
	 * Begins scheduled polling of Piazza Job Status
	 */
	@PostConstruct
	public void startPolling() {
		pollTimer.schedule(pollStatusTask, 10000, POLL_FREQUENCY_SECONDS * (long) 1000);
	}

	public void stopPolling() {
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
						// Kill the Job
						jobService.createJobError(job, "The Job has timed out.");
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
					// Convert the bytes into a Geometry object that Hibernate can store
					InputStream inputStream = new ByteArrayInputStream(detectionBytes);
					GeometryJSON geojson = new GeometryJSON();
					Geometry geometry = geojson.read(inputStream);
					// Commit the Detection to the Detections table
					jobService.createDetection(job, geometry);
					// Finally, mark the Job as successful
					job.setStatus(Job.STATUS_SUCCESS);
				} catch (IOException exception) {
					exception.printStackTrace();
					String error = String.format("Job %s failed because of an internal error while reading the detection geometry.",
							job.getJobId());
					jobService.createJobError(job, error);
					job.setStatus(Job.STATUS_ERROR);
				} catch (UserException exception) {
					exception.printStackTrace();
					String error = String.format("Job %s failed because of an internal error downloading the detection geometry.",
							job.getJobId());
					jobService.createJobError(job, error);
					// Fail the Job as we have failed to download the bytes
					job.setStatus(Job.STATUS_ERROR);
				}
			} else if (status.isStatusError()) {
				job.setStatus(status.getStatus());
				jobService.createJobError(job, status.getErrorMessage());
			}
			// Commit the updates
			jobService.updateJob(job);
		}
	}
}
