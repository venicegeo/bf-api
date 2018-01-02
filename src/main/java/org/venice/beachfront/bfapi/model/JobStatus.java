package org.venice.beachfront.bfapi.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class JobStatus {
	@JsonProperty("job_id") private final String jobId;
	@JsonProperty("status") private final String status;
	
	public JobStatus(String jobId, String status) {
		this.jobId = jobId;
		this.status = status;
	}
	
	public String getJobId() {
		return jobId;
	}
	
	public String getStatus() {
		return status;
	}
}
