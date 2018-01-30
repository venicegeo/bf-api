package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;
import java.util.List;

import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.DbDTO.JobEntry;
import org.venice.beachfront.bfapi.database.DbDTO.JobStatusEntry;

@Service
public class JobDbService {
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

	public JobEntry getJob(String jobId) throws SQLException {
		// TODO
		return null;
	}

	public List<JobStatusEntry> getJobStatusesForInputs(String algorithmId, String sceneId) throws SQLException {
		// TODO
		return null;
	}

	public List<JobEntry> getAllJobs() throws SQLException {
		// TODO
		return null;
	}

	public List<JobEntry> getJobsForScene(String sceneId) throws SQLException {
		// TODO
		return null;
	}

	public List<JobEntry> getJobsForUser(String userId) throws SQLException {
		// TODO
		return null;
	}

	public List<JobEntry> getJobsForInputs(String algorithmId, String algorithmVersion, String sceneId, Boolean computeMask)
			throws SQLException {
		// TODO
		return null;
	}

	public List<JobEntry> getOutstandingJobs() throws SQLException {
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
