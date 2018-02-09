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

import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

import javax.annotation.PostConstruct;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;

/**
 * Scheduling class that manages the constant polling for Status of Shoreline detections Jobs in Piazza
 */
@Component
public class PiazzaJobPoller {
	@Value("${piazza.poll.frequency.seconds}")
	private int POLL_FREQUENCY_SECONDS;

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
				try {
					StatusMetadata status = piazzaService.getJobStatus(job.getJobId());
					processJobStatus(job, status);
				} catch (UserException exception) {
					// TODO - Get the age of the job and determine if a complete failure based on timeout is necessary
					continue;
				}
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

		}
	}
}
