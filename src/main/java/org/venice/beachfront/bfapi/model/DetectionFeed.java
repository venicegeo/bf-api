package org.venice.beachfront.bfapi.model;

import java.util.Collections;
import java.util.List;

import org.joda.time.DateTime;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

public class DetectionFeed {
	@JsonProperty("detectionfeed_id") private final String id;
	@JsonProperty("algorithm_name") private final String algorithmName;
	@JsonProperty("algorithm_version") private final String algorithmVersion;
	@JsonProperty("created_by") private final String createdByUserId;
	@JsonProperty("created_on") private final DateTime createdOn;
	@JsonProperty("expires_on") private final DateTime expiresOn;
	@JsonProperty("interval") private final int intervalSeconds;
	@JsonProperty("name") private final String name;
	@JsonProperty("last_job") private final String lastJobId;
	@JsonProperty("last_complete_job") private final String lastCompleteJobId;
	@JsonProperty("jobs") private final List<String> jobs;
	@JsonProperty("extras") private final JsonNode extras;
	
	/**
	 * @param id
	 * @param algorithmName
	 * @param algorithmVersion
	 * @param createdByUserId
	 * @param createdOn
	 * @param expiresOn
	 * @param intervalSeconds
	 * @param name
	 * @param lastJobId
	 * @param lastCompleteJobId
	 * @param jobs
	 * @param extras
	 */
	public DetectionFeed(String id, String algorithmName, String algorithmVersion, String createdByUserId,
			DateTime createdOn, DateTime expiresOn, int intervalSeconds, String name, String lastJobId,
			String lastCompleteJobId, List<String> jobs, JsonNode extras) {
		this.id = id;
		this.algorithmName = algorithmName;
		this.algorithmVersion = algorithmVersion;
		this.createdByUserId = createdByUserId;
		this.createdOn = createdOn;
		this.expiresOn = expiresOn;
		this.intervalSeconds = intervalSeconds;
		this.name = name;
		this.lastJobId = lastJobId;
		this.lastCompleteJobId = lastCompleteJobId;
		this.jobs = Collections.unmodifiableList(jobs);
		this.extras = extras;
	}

	public String getId() {
		return id;
	}

	public String getAlgorithmName() {
		return algorithmName;
	}

	public String getAlgorithmVersion() {
		return algorithmVersion;
	}

	public String getCreatedByUserId() {
		return createdByUserId;
	}

	public DateTime getCreatedOn() {
		return createdOn;
	}

	public DateTime getExpiresOn() {
		return expiresOn;
	}

	public int getIntervalSeconds() {
		return intervalSeconds;
	}

	public String getName() {
		return name;
	}

	public String getLastJobId() {
		return lastJobId;
	}

	public String getLastCompleteJobId() {
		return lastCompleteJobId;
	}

	public List<String> getJobs() {
		return jobs;
	}

	public JsonNode getExtras() {
		return extras;
	}	
}
