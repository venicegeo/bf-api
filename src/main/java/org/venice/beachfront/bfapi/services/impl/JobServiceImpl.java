package org.venice.beachfront.bfapi.services.impl;

import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.DbDTO.JobEntry;
import org.venice.beachfront.bfapi.database.DbDTO.JobStatusEntry;
import org.venice.beachfront.bfapi.database.JobDbService;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.services.AlgorithmService;
import org.venice.beachfront.bfapi.services.IABrokerService;
import org.venice.beachfront.bfapi.services.JobService;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.util.RawValue;

@Profile("main")
@Service
public class JobServiceImpl implements JobService {
	@Autowired
	private JobDbService jobDbService;
	
	@Autowired
	private AlgorithmService algorithmService;
	
	@Autowired
	private IABrokerService iaBrokerService;
	
	@Override
	public Job createJob(String jobName, 
			String creatorUserId,
			String sceneId,
			String algorithmId,
			String planetApiKey,
			JsonNode extras) {
		
		Algorithm algorithm = this.algorithmService.getAlgorithm(algorithmId);
		Scene scene = this.iaBrokerService.getScene(sceneId, planetApiKey, true);
		this.iaBrokerService.activateScene(scene, planetApiKey);
		
		//String jobId = piazzaService.execute(...)
		String jobId = String.format("%s-%s-%s-%s", creatorUserId, sceneId, algorithmId, DateTime.now().toString());
		
		try {
			this.jobDbService.insertJob(jobId, 
					jobName, 
					algorithm.getServiceId(), 
					algorithm.getName(), 
					algorithm.getVersion(), 
					scene.getId(), 
					"Pending", 
					scene.getTide(),
					scene.getTideMin(),
					scene.getTideMax(),
					creatorUserId);
		} catch (SQLException e) {
			throw new RuntimeException(e);
		}
		return null;
	}

	@Override
	public List<Job> getJobs() {
		List<Job> result = new ArrayList<>();
		try {
			for (JobEntry je : this.jobDbService.getAllJobs()) {
				result.add(new Job(
						je.jobId,
						je.name,
						je.status,
						je.createdBy,
						je.createdOn,
						je.algorithmName,
						je.algorithmVersion,
						JsonNodeFactory.instance.rawValueNode(new RawValue(je.scene.geometryGeoJson)),
						je.scene.sensorName,
						je.scene.capturedOn,
						je.scene.sceneId,
						null, null));
			}
		} catch (SQLException e) {
			throw new RuntimeException(e);
		}
		return result;
	}

	@Override
	public Job getJob(String jobId)
	{
		try {
			JobEntry job = this.jobDbService.getJob(jobId);
			if (job == null) return null;
			return new Job(
					job.jobId, 
					job.name, 
					job.status, 
					job.createdBy, 
					job.createdOn, 
					job.algorithmName, 
					job.algorithmVersion, 
					JsonNodeFactory.instance.rawValueNode(new RawValue(job.scene.geometryGeoJson)), 
					job.scene.sensorName, 
					job.scene.capturedOn, 
					job.scene.sceneId, 
					null, null);
		} catch (SQLException e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public Confirmation deleteJob(Job job) {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId) {
		List<JobStatus> result = new ArrayList<>();
		try {
			for (JobStatusEntry jse : this.jobDbService.getJobsForInputs(algorithmId, sceneId)) {
				result.add(new JobStatus(jse.jobId, jse.status));
			}
		} catch (SQLException e) {
			throw new RuntimeException(e);
		}
		return result;
	}

}
