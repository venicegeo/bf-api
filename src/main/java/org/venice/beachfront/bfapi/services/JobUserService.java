package org.venice.beachfront.bfapi.services;

import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.database.dao.JobUserDao;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobUser;
import org.venice.beachfront.bfapi.model.UserProfile;

import model.logger.Severity;
import util.PiazzaLogger;

@Service
public class JobUserService {
	@Autowired
	private JobUserDao jobUserDao;
	@Autowired
	private JobDao jobDao;
	@Autowired
	private UserProfileDao userProfileDao;
	@Autowired
	private PiazzaLogger piazzaLogger;

	public JobUser createJobUser(String jobId, String userId) {
		Job job = jobDao.findByJobId(jobId);
		UserProfile user = userProfileDao.findByUserId(userId);
		piazzaLogger.log(String.format("Saving Job User with Job ID %s and User ID %s", jobId, userId), Severity.INFORMATIONAL);
		return jobUserDao.save(new JobUser(job, user));
	}

	public List<JobUser> getJobUsers() {
		ArrayList<JobUser> jobUsers = new ArrayList<>();
		Iterable<JobUser> allJobUsers = jobUserDao.findAll();
		allJobUsers.forEach(jobUser -> jobUsers.add(jobUser));
		return jobUsers;
	}

	public Confirmation deleteJobUser(JobUser jobUser) {
		jobUserDao.delete(jobUser);
		return new Confirmation(jobUser.getJobUserPK().getJob().getJobId(), true);
	}

	public List<JobUser> searchByUser(String userId) {
		return jobUserDao.findByJobUserPK_User_UserId(userId);
	}
}
