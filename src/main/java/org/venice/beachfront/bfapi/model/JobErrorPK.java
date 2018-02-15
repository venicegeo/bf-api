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
public class JobErrorPK implements Serializable {
    @JoinColumn(name = "job_id", nullable = false)
    @OnDelete(action = OnDeleteAction.CASCADE)
    @ManyToOne(targetEntity = Job.class)
    @Convert(converter = JobConverter.class, attributeName = "job_id")
    @JsonProperty("job_id")
    protected Job job;

    public JobErrorPK() { super(); }

    public JobErrorPK(Job job) {
        this.job = job;
    }

    public Job getJob() {
        return job;
    }

    public void setJob(Job job) {
        this.job = job;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        JobErrorPK jobUserPK = (JobErrorPK) o;
        return job.getJobId().equals(jobUserPK.job.getJobId());
    }

    @Override
    public int hashCode() {
        return Objects.hash(job.getJobId());
    }
}

