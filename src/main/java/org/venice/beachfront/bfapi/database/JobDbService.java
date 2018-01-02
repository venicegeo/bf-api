package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;
import java.util.List;

import org.venice.beachfront.bfapi.database.DbDTO.JobEntry;
import org.venice.beachfront.bfapi.database.DbDTO.JobStatusEntry;

public interface JobDbService {
	public boolean jobExists(String jobId) throws SQLException;
	public void insertJob(
			String jobId,
			String name,
			String algorithmId,
			String algorithmName,
			String algorithmVersion,
			String sceneId,
			String status,
			double tide,
			double tideMin24h,
			double tideMax24h,
			String userId
			) throws SQLException;
	public void insertJobFailure(String jobId, String executionStep, String message) throws SQLException;
	public void updateJobStatus(String jobId, String status) throws SQLException;
	public JobEntry getJob(String jobId) throws SQLException;
	public List<JobStatusEntry> getJobsForInputs(String algorithmId, String sceneId) throws SQLException;
	public List<JobEntry> getAllJobs() throws SQLException;
	public List<JobEntry> getJobsForScene(String sceneId) throws SQLException;
	public List<JobEntry> getJobsForUser(String userId) throws SQLException;
	public List<JobEntry> getOutstandingJobs() throws SQLException;
	
	public void insertJobUserRelation(String jobId, String userId) throws SQLException;
	public void deleteJobUserRelation(String jobId, String userId) throws SQLException;	
}
