package org.venice.beachfront.bfapi.model;

import java.io.Serializable;
import java.util.Objects;
import javax.persistence.Convert;
import javax.persistence.Embeddable;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.OneToOne;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;
import org.venice.beachfront.bfapi.model.converter.JobConverter;
import org.venice.beachfront.bfapi.model.converter.UserConverter;

@Embeddable
public class JobUserPK implements Serializable {
    @JoinColumn(name = "job_id", nullable = false)
    @OnDelete(action = OnDeleteAction.CASCADE)
    @ManyToOne(targetEntity = Job.class)
    @Convert(converter = JobConverter.class, attributeName = "job_id")
    @JsonProperty("job_id")
    protected Job job;
    @JoinColumn(name = "user_id", nullable = false)
    @OnDelete(action = OnDeleteAction.CASCADE)
    @OneToOne(targetEntity = UserProfile.class)
    @Convert(converter = UserConverter.class, attributeName = "user_id")
    @JsonProperty("user_id")
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

