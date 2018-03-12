/**
 * Copyright 2018, Radiant Solutions, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi.model;

import java.io.Serializable;
import java.util.Objects;

import javax.persistence.Convert;
import javax.persistence.Embeddable;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;

import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;
import org.venice.beachfront.bfapi.model.converter.JobConverter;

import com.fasterxml.jackson.annotation.JsonProperty;

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

