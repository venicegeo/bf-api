package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.IABrokerService.IABrokerNotFoundException;
import org.venice.beachfront.bfapi.services.IABrokerService.IABrokerNotPermittedException;
import org.venice.beachfront.bfapi.services.IABrokerService.IABrokerUnknownException;
import org.venice.beachfront.bfapi.services.IABrokerService.IABrokerUpstreamPlanetErrorException;

import com.fasterxml.jackson.databind.JsonNode;

@Service
public class JobService {
	@Autowired
	private JobDao jobDao;
	@Autowired
	private AlgorithmService algorithmService;
	@Autowired
	private IABrokerService iaBrokerService;

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
		// TODO - need add to broker service

		// Prepare Job Request

		// Dispatch Job to Piazza

		return null;
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
	private String getAlgorithmCli(String algorithmName, List<String> fileNames, String scenePlatform, boolean computeMask) {

		return null;
	}
}
