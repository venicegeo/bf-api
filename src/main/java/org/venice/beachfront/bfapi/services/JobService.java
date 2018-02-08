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
		// Fetch the Algorithm and Scene information; Activate Scene if needed
		Algorithm algorithm = algorithmService.getAlgorithm(algorithmId);
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
		Job job = new Job(jobId, jobName, Job.STATUS_SUBMITTED, creatorUserId, new DateTime(), algorithm.getName(), algorithm.getVersion(),
				scene.getSceneId(), scene.getTide(), scene.getTideMin24H(), scene.getTideMax24H(), extras, computeMask);
		jobDao.save(job);
		return job;
	}

	public List<Job> getJobs() {
		return null; // TODO
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
