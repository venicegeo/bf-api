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

import javax.persistence.Column;
import javax.persistence.Convert;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.Transient;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.converter.TimestampConverter;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

import io.swagger.annotations.ApiModelProperty;

@Entity
@Table(name = "__beachfront__job")
public class Job {
	public static final String STATUS_CANCELLED = "Cancelled";
	public static final String STATUS_ERROR = "Error";
	public static final String STATUS_FAIL = "Fail";
	public static final String STATUS_PENDING = "Pending";
	public static final String STATUS_ACTIVATING = "Activating";
	public static final String STATUS_RUNNING = "Running";
	public static final String STATUS_SUBMITTED = "Submitted";
	public static final String STATUS_SUCCESS = "Success";

	@Id
	@Column(name = "job_id")
	@JsonProperty("job_id")
	@ApiModelProperty(required = true, value = "The unique ID of the Job in correlation with Piazza")
	private String jobId;
	@Column(name = "name")
	@JsonProperty("name")
	@ApiModelProperty(required = true, value = "The user-provided name the job")
	private String jobName;
	@Column(name = "seed_job_id")
	@JsonProperty("seed_job_id")
	@ApiModelProperty(required = false, value = "The Seed Job ID, if this job is a redundant job.")
	private String seedJobId;
	@Column(name = "status")
	@JsonProperty("status")
	@ApiModelProperty(required = true, value = "The current status of the job")
	private String status;
	@Column(name = "created_by")
	@JsonProperty("created_by")
	@ApiModelProperty(required = true, value = "The ID of the first requesting user for this job")
	private String createdByUserId;
	@Convert(converter = TimestampConverter.class)
	@Column(name = "created_on")
	@JsonProperty("created_on")
	@ApiModelProperty(required = true, value = "The date the job was first requested")
	private DateTime createdOn;
	@Column(name = "algorithm_id")
	@JsonProperty("algorithm_id")
	@ApiModelProperty(required = true, value = "The unique ID of the Algorithm used to process this Job")
	private String algorithmId;
	@Column(name = "algorithm_name")
	@JsonProperty("algorithm_name")
	@ApiModelProperty(required = true, value = "The friendly name of the Algorithm used to process this Job")
	private String algorithmName;
	@Column(name = "algorithm_version")
	@JsonProperty("algorithm_version")
	@ApiModelProperty(required = true, value = "The version of the Algorithm used")
	private String algorithmVersion;
	@Column(name = "scene_id")
	@JsonProperty("scene_id")
	@ApiModelProperty(required = true, value = "The unique ID of the Scene used as Job input")
	private String sceneId;
	@Column(name = "tide")
	@JsonProperty("tide")
	@ApiModelProperty(required = true, value = "The current tide information of the Scene")
	private Double tide;
	@Column(name = "tide_min_24h")
	@JsonProperty("tide_min_24h")
	@ApiModelProperty(required = true, value = "24-hour minimum Tide metadata of the Scene")
	private Double tideMin24h;
	@Column(name = "tide_max_24h")
	@JsonProperty("tide_max_24h")
	@ApiModelProperty(required = true, value = "24-hour maximum Tide metadata of the Scene")
	private Double tideMax24h;
	@JsonProperty("extras")
	@Transient // TODO: This must be added to the Liquibase Migrations
	@ApiModelProperty(required = false, value = "User-defined bag of properties used for extra Job input")
	private JsonNode extras;
	@Column(name = "compute_mask")
	@JsonProperty("compute_mask")
	@ApiModelProperty(required = true, value = "Determines if the Algorithm should apply a compute mask for non-coastal areas")
	private Boolean computeMask;

	/**
	 * Default constructor. Required for JPA/Hibernate.
	 */
	public Job() {
		super();
	}

	/**
	 * @param jobId
	 *            job unique ID
	 * @param jobName
	 *            job name
	 * @param status
	 *            job status in Piazza
	 * @param createdByUserId
	 *            ID of user who created the job
	 * @param createdOn
	 *            job creation time
	 * @param algorithmId
	 *            ID of algorithm job is using
	 * @param algorithmName
	 *            name of algorithm job is using
	 * @param algorithmVersion
	 *            version of algorithm job is using
	 * @param sceneId
	 *            scene ID of job imagery
	 * @param tide
	 *            scene tide value
	 * @param tideMin24h
	 *            scene tide 24 hour minimum
	 * @param tideMax24h
	 *            scene tide 24 hour maximum
	 * @param extras
	 *            extra algorithm-dependent data
	 * @param computeMask
	 *            compute mask boolean
	 */
	public Job(String jobId, String jobName, String status, String createdByUserId, DateTime createdOn, String algorithmId,
			String algorithmName, String algorithmVersion, String sceneId, Double tide, Double tideMin24h, Double tideMax24h,
			JsonNode extras, Boolean computeMask) {
		this.jobId = jobId;
		this.jobName = jobName;
		this.status = status;
		this.createdByUserId = createdByUserId;
		this.createdOn = createdOn;
		this.algorithmId = algorithmId;
		this.algorithmName = algorithmName;
		this.algorithmVersion = algorithmVersion;
		this.sceneId = sceneId;
		this.tide = tide;
		this.tideMin24h = tideMin24h;
		this.tideMax24h = tideMax24h;
		this.extras = extras;
		this.computeMask = computeMask;
	}

	public String getJobId() {
		return jobId;
	}

	public void setJobId(String jobId) {
		this.jobId = jobId;
	}

	public String getJobName() {
		return jobName;
	}

	public void setJobName(String jobName) {
		this.jobName = jobName;
	}

	public String getStatus() {
		return status;
	}

	public void setStatus(String status) {
		this.status = status;
	}

	public String getCreatedByUserId() {
		return createdByUserId;
	}

	public void setCreatedByUserId(String createdByUserId) {
		this.createdByUserId = createdByUserId;
	}

	public DateTime getCreatedOn() {
		return createdOn;
	}

	public void setCreatedOn(DateTime createdOn) {
		this.createdOn = createdOn;
	}

	public String getAlgorithmId() {
		return algorithmId;
	}

	public void setAlgorithmId(String algorithmId) {
		this.algorithmId = algorithmId;
	}

	public String getAlgorithmName() {
		return algorithmName;
	}

	public void setAlgorithmName(String algorithmName) {
		this.algorithmName = algorithmName;
	}

	public String getAlgorithmVersion() {
		return algorithmVersion;
	}

	public void setAlgorithmVersion(String algorithmVersion) {
		this.algorithmVersion = algorithmVersion;
	}

	public String getSceneId() {
		return sceneId;
	}

	public void setSceneId(String sceneId) {
		this.sceneId = sceneId;
	}

	public Double getTide() {
		return tide;
	}

	public void setTide(Double tide) {
		this.tide = tide;
	}

	public Double getTideMin24h() {
		return tideMin24h;
	}

	public void setTideMin24h(Double tideMin24h) {
		this.tideMin24h = tideMin24h;
	}

	public Double getTideMax24h() {
		return tideMax24h;
	}

	public void setTideMax24h(Double tideMax24h) {
		this.tideMax24h = tideMax24h;
	}

	public JsonNode getExtras() {
		return extras;
	}

	public void setExtras(JsonNode extras) {
		this.extras = extras;
	}

	public Boolean getComputeMask() {
		return computeMask;
	}

	public String getSeedJobId() {
		return seedJobId;
	}

	public void setSeedJobId(String seedJobId) {
		this.seedJobId = seedJobId;
	}

}
