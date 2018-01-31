package org.venice.beachfront.bfapi.model;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonProperty;

@Entity
@Table(name = "__beachfront__job_status")
public class JobStatus {
	@Id
	@JsonProperty("job_id") private String jobId;
	@JsonProperty("status") private String status;

	public JobStatus() { super(); }

	public JobStatus(String jobId, String status) {
		this.jobId = jobId;
		this.status = status;
	}
	
	public String getJobId() {
		return jobId;
	}

	public void setJobId(String jobId) {
		this.jobId = jobId;
	}

	public String getStatus() {
		return status;
	}

	public void setStatus(String status) {
		this.status = status;
	}
}
