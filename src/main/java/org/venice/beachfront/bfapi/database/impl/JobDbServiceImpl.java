package org.venice.beachfront.bfapi.database.impl;

import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.DbDTO.JobEntry;
import org.venice.beachfront.bfapi.database.DbDTO.JobStatusEntry;
import org.venice.beachfront.bfapi.database.JobDbService;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.model.Job;

@Service
public class JobDbServiceImpl implements JobDbService {
	@Autowired
	private JobDao jobDao;

	@Autowired @Qualifier("insertJob.sql")
	private String insertJobSql;
	
	public void insertJob(Job job) {
		jobDao.save(job);
	}
	
	public Job getJobByJobId(String jobId) {
		return jobDao.findByJobId(jobId);
	}
	
	@Override
	public void insertJob(String jobId, String name, String algorithmId, String algorithmName, String algorithmVersion,
			String sceneId, String status, double tide, double tideMin24h, double tideMax24h, String userId)
			throws SQLException {
		
//		try (
//				PooledConnection pconn = this.connectionManager.getPooledConnection();
//				PreparedStatement stmt = pconn.getConnection().prepareStatement(this.insertJobSql);
//			) {
//			stmt.setString(1, jobId);
//			stmt.setString(2, algorithmId);
//			stmt.setString(3, algorithmName);
//			stmt.setString(4, algorithmVersion);
//			stmt.setString(5, userId);
//			stmt.setString(6, name);
//			stmt.setString(7, sceneId); // verified by foreign key DB schema
//			stmt.setString(8, status);
//			stmt.setDouble(9, tide);
//			stmt.setDouble(10, tideMin24h);
//			stmt.setDouble(11, tideMax24h);
//			stmt.execute();
//		}
	}

	@Autowired @Qualifier("jobExists.sql")
	private String jobExistsSql;
	
	@Override
	public boolean jobExists(String jobId) throws SQLException {
		return false;
//		try (
//				PooledConnection pconn = this.connectionManager.getPooledConnection();
//				PreparedStatement stmt = pconn.getConnection().prepareStatement(this.jobExistsSql);
//			) {
//			stmt.setString(1, jobId);
//			try (ResultSet rs = stmt.executeQuery()) {
//				return rs.next();
//			}
//		}
	}


	@Override
	public void insertJobFailure(String jobId, String executionStep, String message) throws SQLException {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void updateJobStatus(String jobId, String status) throws SQLException {
		// TODO Auto-generated method stub

	}

	@Autowired @Qualifier("selectJob.sql")
	private String selectJobSql;
	
	@Override
	public JobEntry getJob(String jobId) throws SQLException {
		JobEntry result = new JobEntry();
//		try (
//				PooledConnection pconn = this.connectionManager.getPooledConnection();
//				PreparedStatement stmt = pconn.getConnection().prepareStatement(this.selectJobSql);
//			) {
//			stmt.setString(1, jobId);
//			try (ResultSet rs = stmt.executeQuery()) {
//				if (!rs.next()) {
//					return null;
//				}
//				result.jobId = rs.getString("job_id");
//				result.algorithmName = rs.getString("algorithm_name");
//				result.algorithmVersion = rs.getString("algorithm_version");
//				result.createdBy = rs.getString("created_by");
//				result.createdOn = new DateTime(rs.getTimestamp("created_on"));
//				result.name = rs.getString("name");
//				result.status = rs.getString("status");
//				result.tide = rs.getDouble("tide");
//				result.tideMin24h = rs.getDouble("tide_min_24h");
//				result.tideMax24h = rs.getDouble("tide_max_24h");
//				result.errorMessage = rs.getString("error_message");
//				result.executionStep = rs.getString("execution_step");
//
//				result.scene = new SceneEntry();
//				result.scene.sceneId = rs.getString("scene_id");
//				result.scene.geometryGeoJson = rs.getString("geometry");
//				result.scene.sensorName = rs.getString("sensor_name");
//				result.scene.capturedOn = new DateTime(rs.getTimestamp("captured_on"));
//			}
//		}
		return result;
	}

	@Autowired @Qualifier("selectJobByInputs.sql")
	private String selectJobByInputsSql;

	@Override
	public List<JobStatusEntry> getJobsForInputs(String algorithmId, String sceneId) throws SQLException {
		List<JobStatusEntry> result = new ArrayList<>();
//		try (
//				PooledConnection pconn = this.connectionManager.getPooledConnection();
//				PreparedStatement stmt = pconn.getConnection().prepareStatement(this.selectJobByInputsSql);
//			) {
//			stmt.setString(1, algorithmId);
//			stmt.setString(2, sceneId);
//			try (ResultSet rs = stmt.executeQuery()) {
//				while (rs.next()) {
//					JobStatusEntry statusEntry = new JobStatusEntry();
//					statusEntry.jobId = rs.getString(1);
//					statusEntry.status = rs.getString(2);
//					result.add(statusEntry);
//				}		
//			}
//		}
		return result;
	}

	@Override
	public List<JobEntry> getJobsForScene(String sceneId) throws SQLException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public List<JobEntry> getJobsForUser(String userId) throws SQLException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public List<JobEntry> getOutstandingJobs() throws SQLException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void insertJobUserRelation(String jobId, String userId) throws SQLException {
		// TODO Auto-generated method stub

	}

	@Override
	public void deleteJobUserRelation(String jobId, String userId) throws SQLException {
		// TODO Auto-generated method stub

	}

	@Autowired @Qualifier("selectAllJobs.sql")
	private String selectAllJobsSql;

	@Override
	public List<JobEntry> getAllJobs() throws SQLException {
		List<JobEntry> result = new ArrayList<>();
//		try (
//				PooledConnection pconn = this.connectionManager.getPooledConnection();
//				PreparedStatement stmt = pconn.getConnection().prepareStatement(this.selectAllJobsSql);
//			) {
//			try (ResultSet rs = stmt.executeQuery()) {
//				while (rs.next()) {
//					JobEntry jobEntry = new JobEntry();
//					jobEntry.jobId = rs.getString("job_id");
//					jobEntry.algorithmName = rs.getString("algorithm_name");
//					jobEntry.algorithmVersion = rs.getString("algorithm_version");
//					jobEntry.createdBy = rs.getString("created_by");
//					jobEntry.createdOn = new DateTime(rs.getTimestamp("created_on"));
//					jobEntry.name = rs.getString("name");
//					jobEntry.status = rs.getString("status");
//					jobEntry.tide = rs.getDouble("tide");
//					jobEntry.tideMin24h = rs.getDouble("tide_min_24h");
//					jobEntry.tideMax24h = rs.getDouble("tide_max_24h");
//					jobEntry.errorMessage = rs.getString("error_message");
//					jobEntry.executionStep = rs.getString("execution_step");
//
//					jobEntry.scene = new SceneEntry();
//					jobEntry.scene.sceneId = rs.getString("scene_id");
//					jobEntry.scene.geometryGeoJson = rs.getString("geometry");
//					jobEntry.scene.sensorName = rs.getString("sensor_name");
//					jobEntry.scene.capturedOn = new DateTime(rs.getTimestamp("captured_on"));
//					result.add(jobEntry);
//				}
//			}
//		}
		return result;
	}
}
