package org.venice.beachfront.bfapi.services;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.database.dao.JobUserDao;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.model.JobUser;
import org.venice.beachfront.bfapi.model.UserProfile;

@Service
public class JobUserService {
	@Autowired
	private JobUserDao jobUserDao;
	@Autowired
	private JobDao jobDao;
	@Autowired
	private UserProfileDao userProfileDao;

	public JobUser createJobUser(String jobId, String userId) {
		Job job = jobDao.findByJobId(jobId);
		UserProfile user = userProfileDao.findByUserId(userId);
		System.out.println("saving user-job JobID: " + job.getJobId());
		System.out.println("saving user-job UserID: " + user.getUserId());
		return jobUserDao.save(new JobUser(job, user));
	}

	public List<JobUser> getJobUsers() {
		ArrayList<JobUser> jobUsers = new ArrayList<>();
		Iterable<JobUser> allJobUsers = jobUserDao.findAll();
		allJobUsers.forEach(jobUser -> jobUsers.add(jobUser));
		return jobUsers;
	}

	public JobUser getJobUser(String jobId) {
		return jobUserDao.findByJobJobId(jobId);
	}

	public Confirmation deleteJobUser(JobUser jobUser) {
		jobUserDao.delete(jobUser);
		return new Confirmation(
				jobUser.getJob().getJobId(),
				true);
	}

	public List<JobUser> searchByUser(String userId) {
		return jobUserDao.findByUserUserId(userId);
	}
}
