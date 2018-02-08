package org.venice.beachfront.bfapi.model;

import java.io.Serializable;
import java.util.Objects;
import javax.persistence.Convert;

public class JobUserPK implements Serializable {
    @Convert(converter = JobConverter.class)
    protected Job job;
    @Convert(converter = UserConverter.class)
    protected UserProfile user;

    public JobUserPK() { super(); }

    public JobUserPK(Job job, UserProfile user) {
        this.job = job;
        this.user = user;
    }

    public Job getJob() {
        return job;
    }

    public void setJob(Job job) {
        this.job = job;
    }

    public UserProfile getUser() {
        return user;
    }

    public void setUser(UserProfile user) {
        this.user = user;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        JobUserPK jobUserPK = (JobUserPK) o;
        return job.getJobId().equals(jobUserPK.job.getJobId()) &&
                user.getUserId().equals(jobUserPK.user.getUserId());
    }

    @Override
    public int hashCode() {
        return Objects.hash(job.getJobId(), user.getUserId());
    }
}

