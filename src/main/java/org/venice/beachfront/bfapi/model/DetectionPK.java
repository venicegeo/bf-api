package org.venice.beachfront.bfapi.model;

import java.io.Serializable;
import java.util.Objects;
import javax.persistence.Column;
import javax.persistence.Embeddable;
import javax.persistence.JoinColumn;
import javax.persistence.OneToOne;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;

@Embeddable
public class DetectionPK implements Serializable {
    @JoinColumn(name = "job_id", nullable = false, columnDefinition = "VARCHAR(64)")
    @OnDelete(action = OnDeleteAction.CASCADE)
    @OneToOne(targetEntity = Job.class, optional = false)
    @JsonProperty("job_id")
    private Job job;
    @Column(name = "feature_id")
    @JsonProperty("feature_id")
    private int featureId;

    public DetectionPK() { super(); }

    public DetectionPK(Job job, int featureId) {
        this.job = job;
        this.featureId = featureId;
    }

    public Job getJob() {
        return job;
    }

    public void setJob(Job job) {
        this.job = job;
    }

    public int getFeatureId() {
        return featureId;
    }

    public void setFeatureId(int featureId) {
        this.featureId = featureId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DetectionPK detectionPK = (DetectionPK) o;
        return job.getJobId().equals(detectionPK.job.getJobId()) &&
                featureId == detectionPK.featureId;
    }

    @Override
    public int hashCode() {
        return Objects.hash(job.getJobId(), featureId);
    }
}

