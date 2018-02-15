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
import javax.persistence.Column;
import javax.persistence.EmbeddedId;
import javax.persistence.Entity;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonProperty;

@Entity
@Table(name = "__beachfront__job_error")
public class JobError implements Serializable{
	@EmbeddedId
	JobErrorPK jobErrorPK;
	@Column(name = "error_message")
	@JsonProperty("error_message")
	String errorMessage;
	@Column(name = "execution_step")
	@JsonProperty("execution_step")
	String executionStep;

	public JobError() {
		super();
	}

	public JobError(Job job, String errorMessage, String executionStep) {
		this.jobErrorPK = new JobErrorPK(job);
		this.errorMessage = errorMessage;
		this.executionStep = executionStep;
	}

	public JobErrorPK getJobErrorPK() {
		return jobErrorPK;
	}

	public void setJob(JobErrorPK jobErrorPK) {
		this.jobErrorPK = jobErrorPK;
	}

	public String getErrorMessage() {
		return errorMessage;
	}

	public void setErrorMessage(String errorMessage) {
		this.errorMessage = errorMessage;
	}

	public String getExecutionStep() {
		return executionStep;
	}

	public void setExecutionStep(String executionStep) {
		this.executionStep = executionStep;
	}

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        JobError jobError = (JobError) o;
        return Objects.equals(jobError.getJobErrorPK().getJob().getJobId(), jobError.getJobErrorPK().getJob().getJobId()) &&
                Objects.equals(errorMessage, jobError.errorMessage) &&
                Objects.equals(executionStep, jobError.executionStep);
    }

    @Override
    public int hashCode() {
        return Objects.hash(jobErrorPK.getJob().getJobId(), errorMessage, executionStep);
    }

    @Override
    public String toString() {
        return "JobError{" +
                "jobId=" + jobErrorPK.getJob().getJobId() +
                ", errorMessage='" + errorMessage + '\'' +
                ", executionStep='" + executionStep + '\'' +
                '}';
    }
}
