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

