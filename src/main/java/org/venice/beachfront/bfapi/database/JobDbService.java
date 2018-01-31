package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;

@Service
public class JobDbService {
	@Autowired
	private JobDao jobDao;

	public boolean jobExists(String jobId) throws SQLException {
		// TODO
		return false;
	}

	public void insertJob(String jobId, String name, String algorithmId, String algorithmName, String algorithmVersion, String sceneId,
			String status, double tide, double tideMin24h, double tideMax24h, String userId, Boolean computeMask) throws SQLException {
		// TODO
	}

	public void insertJobFailure(String jobId, String executionStep, String message) throws SQLException {
		// TODO
	}

	public void updateJobStatus(String jobId, String status) throws SQLException {
		// TODO
	}

	public Job getJob(String jobId) {
		return jobDao.findByJobId(jobId);
	}

	public List<JobStatus> getJobStatusesForInputs(String algorithmId, String sceneId) throws SQLException {
		// TODO
		return null;
	}

	public List<Job> getAllJobs() throws SQLException {
		// TODO
		return null;
	}

	public List<Job> getJobsForScene(String sceneId) throws SQLException {
		// TODO
		return null;
	}

	public List<Job> getJobsForUser(String userId) throws SQLException {
		// TODO
		return null;
	}

	public List<Job> getJobsForInputs(String algorithmId, String algorithmVersion, String sceneId, Boolean computeMask)
			throws SQLException {
		// TODO
		return null;
	}

	public List<Job> getOutstandingJobs() throws SQLException {
		// TODO
		return null;
	}

	public void insertJobUserRelation(String jobId, String userId) throws SQLException {
		// TODO
	}

	public void deleteJobUserRelation(String jobId, String userId) throws SQLException {
		// TODO
	}
}
