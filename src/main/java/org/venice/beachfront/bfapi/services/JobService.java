package org.venice.beachfront.bfapi.services;

import java.io.IOException;
import java.io.StringWriter;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

import org.geotools.geojson.geom.GeometryJSON;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
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

import com.fasterxml.jackson.databind.JsonNode;
import com.vividsolutions.jts.geom.Geometry;

@Service
public class JobService {
	@Value("${gpkg.converter.protocol}")
	private String GPKG_CONVERTER_PROTOCOL;
	@Value("${gpkg.converter.server}")
	private String GPKG_CONVERTER_SERVER;
	@Value("${gpkg.converter.port}")
	private int GPKG_CONVERTER_PORT;	
			
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
	private RestTemplate restTemplate;

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
		// Fetch the Algorithm
		Algorithm algorithm = algorithmService.getAlgorithm(algorithmId);
		// First step is to check for any existing Jobs that match these parameters exactly. If so, then simply return
		// that Job.
		Job redundantJob = getExistingRedundantJob(sceneId, algorithm, computeMask);
		if (redundantJob != null) {
			jobUserDao.save(new JobUser(redundantJob, userProfileService.getUserProfileById(creatorUserId)));
			return redundantJob;
		}

		// Fetch Scene Information
		Scene scene = null;
		try {
			scene = sceneService.getScene(sceneId, planetApiKey, true);
		} catch (Exception exception) {
			throw new UserException("There was an error getting the scene information.", exception.getMessage(), null);
		}
		try {
			sceneService.activateScene(scene, planetApiKey);
		} catch (Exception exception) {
			throw new UserException("There was an error activating the requested scene.", exception.getMessage(), null);
		}

		// Re-fetch scene after activation
		try {
			scene = sceneService.getScene(sceneId, planetApiKey, true);
		} catch (Exception exception) {
			throw new UserException("There was an error getting the scene information.", exception.getMessage(), null);
		}

		// Formulate the URLs for the Scene
		List<String> fileNames = sceneService.getSceneInputFileNames(scene);
		List<String> fileUrls = sceneService.getSceneInputURLs(scene);

		// Prepare Job Request
		String algorithmCli = getAlgorithmCli(algorithm.getName(), fileNames, scene.getSensorName(), computeMask);

		// Dispatch Job to Piazza
		String jobId = piazzaService.execute(algorithm.getServiceId(), algorithmCli, fileNames, fileUrls, creatorUserId);

		// Create Job and commit to database; return to User
		Job job = new Job(jobId, jobName, Job.STATUS_SUBMITTED, creatorUserId, new DateTime(), algorithm.getServiceId(),
				algorithm.getName(), algorithm.getVersion(), scene.getSceneId(), scene.getTide(), scene.getTideMin24H(),
				scene.getTideMax24H(), extras, computeMask);
		// Save the Job to the Jobs table
		jobDao.save(job);
		// Associate this Job with the User who requested it
		jobUserDao.save(new JobUser(job, userProfileService.getUserProfileById(creatorUserId)));
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
	 * Gets the list of all outstanding jobs. That is, jobs that are submitted, running, or pending.
	 * 
	 * @return List of all jobs that are in a non-complete state that are eligible to be polled for updated status.
	 */
	public List<Job> getOutstandingJobs() {
		List<String> outstandingStatuses = new ArrayList<String>();
		outstandingStatuses.add(Job.STATUS_PENDING);
		outstandingStatuses.add(Job.STATUS_RUNNING);
		outstandingStatuses.add(Job.STATUS_SUBMITTED);
		return jobDao.findByStatusIn(outstandingStatuses);
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
		// Query for the existing Job that matches these parameters
		List<Job> jobs = jobDao.findBySceneIdAndAlgorithmIdAndAlgorithmVersionAndComputeMaskAndStatus(sceneId, algorithm.getServiceId(),
				algorithm.getVersion(), computeMask, Job.STATUS_SUCCESS);
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
		List<Job> jobs = new ArrayList<Job>();
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
		List<Job> jobs = new ArrayList<Job>();
		for (JobUser jobRef : jobRefs) {
			jobs.add(jobRef.getJobUserPK().getJob());
		}
		return jobs;
	}

	public Job getJob(String jobId) {
		return jobDao.findByJobId(jobId);
	}

	public Confirmation forgetJob(String jobId, String userId) {
		JobUser jobUser = jobUserDao.findByJobUserPK_Job_JobIdAndJobUserPK_User_UserId(jobId, userId);
		if (jobUser != null) {
			jobUserDao.delete(jobUser);
			return new Confirmation(jobId, true);
		} else {
			return new Confirmation(jobId, false);
		}
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
		JobError jobError = new JobError(job, error, "Processing");
		jobErrorDao.save(jobError);
	}

	/**
	 * Gets the raw GeoJSON for a detection based on the Job ID
	 * 
	 * @param jobId
	 *            The ID of the Job
	 * @return The GeoJSON detection for the job
	 */
	public byte[] getDetectionGeoJson(String jobId) throws UserException {
		// Find the Detection
		Detection detection = detectionDao.findByDetectionPK_Job_JobId(jobId);
		if (detection == null) {
			throw new UserException(String.format("Could not find any detection for Job %s", jobId), HttpStatus.NOT_FOUND);
		}
		// Get the raw GeoJSON bytes from the Detection Geometry
		Geometry geometry = detection.getGeometry();
		GeometryJSON geojson = new GeometryJSON();
		StringWriter writer = new StringWriter();
		try {
			geojson.write(geometry, writer);
			return writer.toString().getBytes();
		} catch (IOException exception) {
			exception.printStackTrace();
			throw new UserException(String.format("There was an error reading the detection for Job %s.", jobId), exception,
					HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}
	
	/**
	 * Gets the detection data as a GPKG archive for a detection based on the Job ID
	 * 
	 * @param jobId
	 *            The ID of the Job
	 * @return The GPKG archive for the job
	 */
	public byte[] getDetectionGeoPackage(String jobId) throws UserException {
		byte[] geoJsonData = this.getDetectionGeoJson(jobId);		
		HttpHeaders headers = new HttpHeaders();
		headers.setContentType(MediaType.APPLICATION_JSON);
		HttpEntity<byte[]> request = new HttpEntity<byte[]>(geoJsonData, headers);
		
		URI geoJsonToGpkgUri = UriComponentsBuilder.newInstance()
				.scheme(this.GPKG_CONVERTER_PROTOCOL)
				.host(this.GPKG_CONVERTER_SERVER)
				.port(this.GPKG_CONVERTER_PORT)
				.pathSegment("convert")
				.build().toUri();

		ResponseEntity<byte[]> response;
		try {
			response = this.restTemplate.exchange(geoJsonToGpkgUri, HttpMethod.POST, request, byte[].class);
		} catch (RestClientException ex) {
			throw new UserException("Error communicating with GeoPackage converter service", ex, HttpStatus.BAD_GATEWAY);
		}
		
		String contentType = response.getHeaders().getContentType().toString();
		if (!contentType.equals("application/x-sqlite3")) {
			throw new UserException("Unexpected content type from GeoPackage converter service: " + contentType, HttpStatus.BAD_GATEWAY);
		}
		
		return geoJsonData;
	}

	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId) {
		List<Job> jobs = jobDao.findByAlgorithmIdAndSceneId(algorithmId, sceneId);
		List<JobStatus> statuses = new ArrayList<JobStatus>();
		for (Job job : jobs) {
			statuses.add(new JobStatus(job.getJobId(), job.getStatus()));
		}
		return statuses;
	}

	/**
	 * Gets the algorithm CLI command that will be passed to the algorithm through Piazza
	 * 
	 * @param algorithmName
	 *            The name of the algorithm
	 * @param fileNames
	 *            The array of file names
	 * @param scenePlatform
	 *            The scene platform (source)
	 * @param computeMask
	 *            True if compute mask is to be applied, false if not
	 * @return The full command line string that can be executed by the Service Executor
	 */
	private String getAlgorithmCli(String algorithmId, List<String> fileUrls, String scenePlatform, boolean computeMask) {
		List<String> imageFlags = new ArrayList<String>();
		// Generate the images string parameters
		for (String fileUrl : fileUrls) {
			imageFlags.add(String.format("-i %s", fileUrl));
		}
		// Generate Bands based on the platform
		String bandsFlag = null;
		switch (scenePlatform) {
		case Scene.PLATFORM_LANDSAT:
		case Scene.PLATFORM_SENTINEL:
			bandsFlag = "--bands 1 1";
			break;
		case Scene.PLATFORM_PLANETSCOPE:
			bandsFlag = "--bands 2 4";
			break;
		case Scene.PLATFORM_RAPIDEYE:
			bandsFlag = "--bands 2 5";
			break;
		}
		// Piece together the CLI
		StringBuilder command = new StringBuilder();
		command.append(String.join(" ", imageFlags));
		if (bandsFlag != null) {
			command.append(" ");
			command.append(bandsFlag);
		}
		command.append(" --basename shoreline --smooth 1.0");
		if (computeMask) {
			command.append(" --coastmask");
		}
		return command.toString();
	}

}
