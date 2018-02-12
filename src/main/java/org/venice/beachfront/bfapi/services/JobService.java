package org.venice.beachfront.bfapi.services;

import java.util.ArrayList;
import java.util.List;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.fasterxml.jackson.databind.JsonNode;

@Service
public class JobService {
	@Autowired
	private JobDao jobDao;
	@Autowired
	private AlgorithmService algorithmService;
	@Autowired
	private IABrokerService iaBrokerService;
	@Autowired
	private PiazzaService piazzaService;

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
			// Add this Job to the Users Job table
			// TODO - John help with adding job to users table
			return redundantJob;
		}

		// Fetch Scene Information
		Scene scene = null;
		try {
			scene = iaBrokerService.getScene(sceneId, planetApiKey, true);
		} catch (Exception exception) {
			throw new UserException("There was an error getting the scene information.", exception.getMessage(), null);
		}
		try {
			iaBrokerService.activateScene(scene, planetApiKey);
		} catch (Exception exception) {
			throw new UserException("There was an error activating the requested scene.", exception.getMessage(), null);
		}

		// Formulate the URLs for the Scene
		// TODO - need add to broker service - Filip
		List<String> fileNames = new ArrayList<String>(); // TODO - Filip
		List<String> fileUrls = new ArrayList<String>(); // TODO - Filip

		// Prepare Job Request
		String algorithmCli = getAlgorithmCli(algorithm.getName(), fileNames, scene.getSensorName(), computeMask);

		// Dispatch Job to Piazza
		String jobId = piazzaService.execute(algorithm.getServiceId(), algorithmCli, fileNames, fileUrls, creatorUserId);

		// Create Job and commit to database; return to User
		Job job = new Job(jobId, jobName, Job.STATUS_SUBMITTED, creatorUserId, new DateTime(), algorithm.getName(), algorithm.getName(),
				algorithm.getVersion(), scene.getSceneId(), scene.getTide(), scene.getTideMin24H(), scene.getTideMax24H(), extras,
				computeMask);
		jobDao.save(job);
		// TODO: John how do I commit to user job table here
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

	public Job getJob(String jobId) {
		return jobDao.findByJobId(jobId);
	}

	public Confirmation deleteJob(Job job) {
		return null; // TODO
	}

	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId) {
		return null; // TODO
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
