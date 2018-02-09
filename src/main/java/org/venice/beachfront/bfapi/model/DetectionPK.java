package org.venice.beachfront.bfapi.model;

import java.io.Serializable;
import java.util.Objects;
import javax.persistence.Convert;

import com.fasterxml.jackson.annotation.JsonProperty;

public class DetectionPK implements Serializable {
    @JsonProperty("job_id")
    protected Job job;
    @JsonProperty("feature_id")
    protected int featureId;

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

