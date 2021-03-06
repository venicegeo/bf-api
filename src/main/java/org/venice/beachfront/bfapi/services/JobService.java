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

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import org.geotools.geojson.geom.GeometryJSON;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.DetectionDao;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.database.dao.JobErrorDao;
import org.venice.beachfront.bfapi.database.dao.JobUserDao;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Detection;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobError;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.model.JobUser;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;
import org.venice.beachfront.bfapi.services.converter.GeoPackageConverter;
import org.venice.beachfront.bfapi.services.converter.ShapefileConverter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.vividsolutions.jts.geom.Geometry;

import model.logger.Severity;
import util.PiazzaLogger;

@Service
public class JobService {
	@Value("${block.redundant.job.check}")
	private Boolean blockRedundantJobCheck;
	@Value("${block.redundant.job.check.extras.name}")
	private String BLOCK_REDUNDANT_JOB_EXTRAS_NAME;

	@Autowired
	private JobDao jobDao;
	@Autowired
	private JobUserDao jobUserDao;
	@Autowired
	private DetectionDao detectionDao;
	@Autowired
	private JobErrorDao jobErrorDao;
	@Autowired
	private UserProfileService userProfileService;
	@Autowired
	private AlgorithmService algorithmService;
	@Autowired
	private SceneService sceneService;
	@Autowired
	private PiazzaService piazzaService;
	@Autowired
	private PiazzaLogger piazzaLogger;
	@Autowired
	private ObjectMapper objectMapper;
	@Autowired
	private GeoPackageConverter geoPackageConverter;
	@Autowired
	private ShapefileConverter shpConverter;

	/**
	 * Creates a Beachfront Job. This will submit the Job request to Piazza, fetch the Job ID, and add all of the Job
	 * information into the Jobs DB Table. Polling will then begin for this Job's status in order to determine when the
	 * job has completed in Piazza.
	 * 
	 * @param jobName
	 *            The name of the Job
	 * @param creatorUserId
	 *            The ID of the User who created the job
	 * @param sceneId
	 *            The ID of the scene
	 * @param algorithmId
	 *            The ID of the algorithm
	 * @param planetApiKey
	 *            The users Planet Labs key
	 * @param computeMask
	 *            True if the compute mask for the algorithm should be applied, false if not
	 * @param extras
	 *            The JSON Extras
	 * @return The fully created (and already committed) Job object
	 */
	public Job createJob(String jobName, String creatorUserId, String sceneId, String algorithmId, String planetApiKey, Boolean computeMask,
			JsonNode extras) throws UserException {
		piazzaLogger.log(String.format("Processing Job Request for Job %s by user %s for Scene %s on Algorithm %s.", jobName, creatorUserId,
				sceneId, algorithmId), Severity.INFORMATIONAL);
		// Fetch the Algorithm
		Algorithm algorithm = algorithmService.getAlgorithm(algorithmId);
		// First step is to check for any existing Jobs that match these parameters exactly. If so, then simply return
		// that Job.
		if (doBlockRedundantJobs(extras) == false) {
			Job redundantJob = getExistingRedundantJob(sceneId, algorithm, computeMask);
			if (redundantJob != null) {
				// Create a New Job
				String newJobId = UUID.randomUUID().toString();
				Job job = new Job(newJobId, jobName, redundantJob.getStatus(), creatorUserId, new DateTime(), algorithm.getServiceId(),
						algorithm.getName(), algorithm.getVersion(), redundantJob.getSceneId(), redundantJob.getTide(),
						redundantJob.getTideMin24h(), redundantJob.getTideMax24h(), extras, computeMask);
				// Create a link to the Seed Job
				job.setSeedJobId(redundantJob.getJobId());
				piazzaLogger.log(
						String.format(
								"Found Redundant Job %s for %s's Job %s request. Created new Job %s with reference to Seed Job %s. This detection will be reused as the Seed Job",
								redundantJob.getJobId(), creatorUserId, jobName, job.getJobId(), job.getSeedJobId()),
						Severity.INFORMATIONAL);
				// Save the Job to the Jobs table and link to the user
				jobDao.save(job);
				jobUserDao.save(new JobUser(job, userProfileService.getUserProfileById(creatorUserId)));
				return job;
			}
		}

		// Fetch Scene Information
		Scene scene = sceneService.getScene(sceneId, planetApiKey, true);
		// Request Scene activation.
		sceneService.activateScene(scene, planetApiKey);

		// Generate a unique ID for this Job that Piazza and Beachfront will both use to reference.
		String jobId = UUID.randomUUID().toString();

		// Create Job and commit to database; return to User
		Job job = new Job(jobId, jobName, Job.STATUS_ACTIVATING, creatorUserId, new DateTime(), algorithm.getServiceId(),
				algorithm.getName(), algorithm.getVersion(), scene.getSceneId(), scene.getTide(), scene.getTideMin24H(),
				scene.getTideMax24H(), extras, computeMask);

		// Save the Job to the Jobs table
		jobDao.save(job);
		// Associate this Job with the User who requested it
		jobUserDao.save(new JobUser(job, userProfileService.getUserProfileById(creatorUserId)));
		piazzaLogger.log(String.format("Saved Job ID %s for Job %s by User %s", jobId, jobName, creatorUserId), Severity.INFORMATIONAL);

		// Dispatch Job to Piazza. The provided callback will allow Piazza to update the status, once submitted.
		piazzaService.execute(algorithm.getServiceId(), algorithm, creatorUserId, jobId, computeMask, jobName,
				sceneService.asyncGetActiveScene(sceneId, planetApiKey, true), new JobStatusCallback() {
					@Override
					public void updateStatus(String jobId, String status, String errorMessage) {
						Job job = getJob(jobId);
						job.setStatus(status);
						updateJob(job);
						// If the job failed, then ensure that the error message gets recorded
						if ((status.equals(Job.STATUS_ERROR)) && (errorMessage != null)) {
							createJobError(job, errorMessage);
						}
					}
				});

		// Return Job Information
		return job;
	}

	/**
	 * Creates or Updates a Job in the Database
	 * 
	 * @param job
	 *            The fully populated Job object.
	 */
	public void updateJob(Job job) {
		jobDao.save(job);
	}

	/**
	 * Gets the list of all outstanding jobs. That is, jobs that are submitted, running, pending, or activating.
	 * 
	 * @return List of all jobs that are in a non-complete state that are eligible to be polled for updated status.
	 */
	public List<Job> getOutstandingJobs() {
		List<String> outstandingStatuses = new ArrayList<>();
		outstandingStatuses.add(Job.STATUS_PENDING);
		outstandingStatuses.add(Job.STATUS_RUNNING);
		outstandingStatuses.add(Job.STATUS_SUBMITTED);
		outstandingStatuses.add(Job.STATUS_ACTIVATING);
		List<Job> jobs = jobDao.findByStatusIn(outstandingStatuses);
		piazzaLogger.log(String.format("Queried for outstanding Piazza Jobs. Found %s outstanding jobs.", jobs.size()),
				Severity.INFORMATIONAL);
		return jobs;
	}

	/**
	 * If a Job exists in the system that has the specified parameters, then that Job will be returned. If no job exists
	 * matching these parameters, then no Job (null) will be returned. This is used in checking if a new Job should be
	 * created, or if an existing Job should simply be linked instead.
	 * 
	 * @param sceneId
	 *            The Scene ID
	 * @param algorithmId
	 *            The Algorithm ID
	 * @param computeMask
	 *            The compute mask flag
	 * @return Job if one exists, or null if none exist
	 */
	private Job getExistingRedundantJob(String sceneId, Algorithm algorithm, Boolean computeMask) throws UserException {
		// Query for the existing Job that matches these parameters. Will not return jobs that have a Seed Job ID, which
		// means that only original Jobs (not redundant jobs) will be returned.
		List<Job> jobs = jobDao.findBySceneIdAndAlgorithmIdAndAlgorithmVersionAndComputeMaskAndStatusAndSeedJobIdIsNull(sceneId,
				algorithm.getServiceId(), algorithm.getVersion(), computeMask, Job.STATUS_SUCCESS);
		if (jobs.size() > 0) {
			// If any identical Jobs matched, return the Job Metadata. If there are more than one (there should never
			// be) then they are all identical anyways, so just return the first one.
			return jobs.get(0);
		}
		return null;
	}

	/**
	 * Gets a list of all Jobs. Not paginated.
	 * 
	 * @return All jobs.
	 */
	public List<Job> getJobs() {
		List<Job> jobs = new ArrayList<>();
		jobDao.findAll().forEach(jobs::add);
		return jobs;
	}

	/**
	 * Gets a list of all Jobs held by the specified user. Not paginated. This can include jobs created by the user, or
	 * jobs added to that users table by way of redundant jobs.
	 * 
	 * @param createdByUserId
	 *            The user.
	 * @return Jobs owned by the specific user
	 */
	public List<Job> getJobsForUser(String createdByUserId) {
		List<JobUser> jobRefs = jobUserDao.findByJobUserPK_User_UserId(createdByUserId);
		List<Job> jobs = new ArrayList<>();
		for (JobUser jobRef : jobRefs) {
			jobs.add(jobRef.getJobUserPK().getJob());
		}
		piazzaLogger.log(String.format("Queried Jobs for user %s. Found %s Jobs.", createdByUserId, jobs.size()), Severity.INFORMATIONAL);
		return jobs;
	}

	/**
	 * The Jobs list in Beachfront expects raw GeoJSON. The feature is the scene geometry, while the properties are that
	 * of the job and scene combined. This method will return the GeoJSON form of the Jobs array.
	 * 
	 * @param jobs
	 *            The Jobs to convert into a FeatureCollection GeoJSON
	 * @return The GeoJSON representing all of the user jobs, where the geometry is the polygon of the scene footprint
	 */
	public JsonNode getJobsGeoJson(List<Job> userJobs) throws UserException {
		// Wrapper for the Job FeatureCollection
		ObjectNode response = objectMapper.createObjectNode();
		ObjectNode jobWrapper = objectMapper.createObjectNode();
		jobWrapper.put("type", "FeatureCollection");
		// Create Feature Collection for each Job
		ArrayNode features = objectMapper.createArrayNode();
		for (Job job : userJobs) {
			features.add(convertJobToGeoJsonFeature(job));
		}
		jobWrapper.set("features", features);
		response.set("jobs", jobWrapper);
		return response;
	}

	public JsonNode getJobGeoJson(Job job) throws UserException {
		ObjectNode response = objectMapper.createObjectNode();
		response.set("job", convertJobToGeoJsonFeature(job));
		return response;
	}

	/**
	 * Converts a Job object into a single GeoJSON Feature. The geometry will be the Polygon bounding box of the Scene
	 * use to create the job.
	 * 
	 * @param job
	 *            The Job object
	 * @return GeoJSON Feature
	 */
	private ObjectNode convertJobToGeoJsonFeature(Job job) throws UserException {
		GeometryJSON geometryJson = new GeometryJSON();
		// Create the Feature object for this Job
		ObjectNode jobFeature = objectMapper.createObjectNode();
		jobFeature.put("type", "Feature");
		jobFeature.put("id", job.getJobId());
		// Add the Geometry from the Scene used to create this job
		Scene scene = sceneService.getSceneFromLocalDatabase(job.getSceneId());
		if (scene != null) {
			String sceneGeometry = geometryJson.toString(scene.getGeometry());
			try {
				JsonNode geometry = objectMapper.readTree(sceneGeometry);
				jobFeature.set("geometry", geometry);
			} catch (IOException exception) {
				String error = String.format(
						"Could not populate Jobs GeoJSON. Error converting Geometry from Scene %s as stored in the database.",
						scene.getSceneId());
				piazzaLogger.log(error, Severity.ERROR);
				throw new UserException(error, exception, HttpStatus.INTERNAL_SERVER_ERROR);
			}
		} else {
			String error = String.format(
					"Could not populate Jobs GeoJSON, because the Scene information for Scene %s was not present in the database.",
					job.getSceneId());
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, HttpStatus.INTERNAL_SERVER_ERROR);
		}
		// Add the properties to the Feature
		ObjectNode properties = objectMapper.valueToTree(job);
		// Explicit Date Set for proper format
		properties.put("created_on", job.getCreatedOn().toString());
		properties.put("type", "JOB");
		properties.put("time_of_collect", scene.getCaptureTime().toString());
		// On a failed job, Insert error information on failed jobs
		if (Job.STATUS_ERROR.equals(job.getStatus())) {
			JobError jobError = jobErrorDao.findByJobErrorPK_Job_JobId(job.getJobId());
			if (jobError != null) {
				properties.put("errorDetails", jobError.getErrorMessage());
			}
		}
		jobFeature.set("properties", properties);
		return jobFeature;
	}

	public Job getJob(String jobId) {
		return jobDao.findByJobId(jobId);
	}

	public Confirmation forgetJob(String jobId, String userId) {
		JobUser jobUser = jobUserDao.findByJobUserPK_Job_JobIdAndJobUserPK_User_UserId(jobId, userId);
		if (jobUser != null) {
			jobUserDao.delete(jobUser);
			piazzaLogger.log(String.format("User %s has forgotten Job %s", userId, jobId), Severity.INFORMATIONAL);
			return new Confirmation(jobId, true);
		} else {
			piazzaLogger.log(String.format("User %s tried to forget Job %s, but the Job User could not be found.", userId, jobId),
					Severity.ERROR);
			return new Confirmation(jobId, false);
		}
	}

	public Confirmation forgetAllJobs(String userId) throws UserException {
		List<Job> jobs = getJobsForUser(userId);
		for (Job job : jobs) {
			Confirmation confirmation = forgetJob(job.getJobId(), userId);
			if (confirmation.getSuccess() == false) {
				throw new UserException(String.format("Could not delete Job %s for User %s. Something went wrong.", job.getJobId(), userId),
						HttpStatus.INTERNAL_SERVER_ERROR);
			}
		}
		return new Confirmation("delete jobs", true);
	}

	/**
	 * Creates a Detection entry to associate the detection geometry with the Job object
	 * 
	 * @param job
	 *            The Job associated with the detection
	 * @param geometry
	 *            The shoreline detection
	 */
	public void createDetection(Job job, Geometry geometry) {
		detectionDao.save(new Detection(job, 0, geometry));
	}

	/**
	 * Creates an entry in the Job Error Table
	 * 
	 * @param job
	 *            The Job that errored out
	 * @param error
	 *            The error encountered
	 */
	public void createJobError(Job job, String error) {
		// Errors should be short. It's restricted to 64. All generated errors should be simple and straightforward.
		// If truncation becomes a problem, then it should be reduced at the source - not modifying the length.
		if (error.length() > 64) {
			error = error.substring(0, 64);
		}
		JobError jobError = new JobError(job, error, "Processing");
		jobErrorDao.save(jobError);
		piazzaLogger.log(String.format("Recorded Job error for Job %s (%s) with Error %s", job.getJobId(), job.getJobName(), error),
				Severity.ERROR);
	}

	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId) {
		List<Job> jobs = jobDao.findByAlgorithmIdAndSceneId(algorithmId, sceneId);
		List<JobStatus> statuses = new ArrayList<>();
		for (Job job : jobs) {
			statuses.add(new JobStatus(job.getJobId(), job.getStatus()));
		}
		return statuses;
	}

	/**
	 * Determines if the Redundant Job Check should be blocked. This is either determined globally by the redundant flag
	 * environment variable, which will block all jobs - or individually via an individual job request.
	 * <p>
	 * The Redundant Job Check for the specific Job will override the environment variable in all cases.
	 * 
	 * @param extras
	 */
	private boolean doBlockRedundantJobs(JsonNode extras) {
		if (extras != null && extras.has(BLOCK_REDUNDANT_JOB_EXTRAS_NAME)) {
			return extras.get(BLOCK_REDUNDANT_JOB_EXTRAS_NAME).asBoolean();
		} else {
			return blockRedundantJobCheck;
		}
	}

	public static enum DownloadDataType {
		GEOJSON, GEOPACKAGE, SHAPEFILE
	}

	/**
	 * Downloads the results of a job as GeoJSON, GeoPackage, or Shapefile. If the job is incomplete, or otherwise
	 * encountered an error, throws an appropriate UserException.
	 * 
	 * @param jobId
	 *            The job ID
	 * @return byte array with job data
	 */
	public byte[] downloadJobData(String jobId, DownloadDataType dataType) throws UserException {
		this.piazzaLogger.log(String.format("Querying Piazza for status of Job %s", jobId), Severity.INFORMATIONAL);
		String detectionJobId = jobId;
		Job job = getJob(jobId);
		boolean isSeedJob = false;
		// If this is a normal non-redundant Job, then the Job ID will be used to fetch detection bytes. However, if
		// this is a Redundant Job (contains a Seed Job) then that Seed Job ID will be used to get the detection bytes.
		if (job.getSeedJobId() != null) {
			piazzaLogger.log(String.format("Fetching Detection bytes for Redundant Job %s from Seed Job %s", jobId, job.getSeedJobId()),
					Severity.INFORMATIONAL);
			detectionJobId = job.getSeedJobId();
			isSeedJob = true;
		}

		// Ensure the underlying Piazza Detection Job ID has a Successful status
		StatusMetadata statusMetadata = this.piazzaService.getJobStatus(detectionJobId);

		if (statusMetadata.isStatusError()) {
			throw new UserException(statusMetadata.getErrorMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
		}
		if (statusMetadata.isStatusIncomplete()) {
			throw new UserException("Job not finished yet", HttpStatus.NOT_FOUND);
		}
		if (statusMetadata.isStatusSuccess()) {
			// The query depends on if this is a Seed Job or not.
			byte[] geoJsonBytes = isSeedJob ? detectionDao.findFullDetectionGeoJsonFromSeedJob(jobId).getBytes()
					: detectionDao.findFullDetectionGeoJson(jobId).getBytes();
			switch (dataType) {
			case GEOJSON:
				return geoJsonBytes;
			case GEOPACKAGE:
				return geoPackageConverter.apply(geoJsonBytes);
			case SHAPEFILE:
				return shpConverter.apply(geoJsonBytes, job.getJobName());
			}
			throw new UserException("Unknown download data type: " + dataType, HttpStatus.INTERNAL_SERVER_ERROR);
		}
		throw new UserException("Unknown job status: " + statusMetadata.getStatus(), HttpStatus.INTERNAL_SERVER_ERROR);
	}

	/**
	 * Callback used to allow other Services to invoke the Job status update logic from this component.
	 */
	public interface JobStatusCallback {
		/**
		 * Update the Status of a Job
		 * 
		 * @param jobId
		 *            The Job ID
		 * @param status
		 *            The Status of the Job
		 * @param errorMessage
		 *            Error message contents, if status is an error
		 */
		public void updateStatus(String jobId, String status, String errorMessage);
	}
}
