package org.venice.beachfront.bfapi.model;

import org.joda.time.DateTime;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;

public class Job {
	@JsonProperty("job_id") private final String jobId;
	@JsonProperty("name") private final String jobName;
	@JsonProperty("status") private final String status;
	@JsonProperty("created_by") private final String createdByUserId;
	@JsonProperty("created_on") private final DateTime createdOn;
	@JsonProperty("algorithm_name") private final String algorithmName;
	@JsonProperty("algorithm_version")private final String algorithmVersion;
	@JsonProperty("geometry") private final Object geometry;
	@JsonProperty("scene_sensor_name") private final String sceneSensorName;
	@JsonProperty("scene_time_of_collect") private final DateTime sceneTimeOfCollection;
	@JsonProperty("scene_id") private final String sceneId;
	@JsonProperty("extras") private final Object extras;
	@JsonIgnore private final String planetApiKey;
	
	/**
	 * @param jobId job unique ID
	 * @param jobName job name
	 * @param status job status in Piazza
	 * @param createdByUserId ID of user who created the job
	 * @param createdOn job creation time
	 * @param algorithmName name (ID) of algorithm job is using
	 * @param algorithmVersion version of algorithm job is using
	 * @param geometry GeoJSON geometry describing the job
	 * @param sceneSensorName name of sensor source for job imagery
	 * @param sceneTimeOfCollection collection time of job imagery
	 * @param sceneId scene ID of job imagery
	 * @param extras extra algorithm-dependent data
	 * @param planetApiKey API key to use when contacting the Planet Labs API
	 */
	public Job(String jobId, String jobName, String status, String createdByUserId, DateTime createdOn, String algorithmName,
			String algorithmVersion, Object geometry, String sceneSensorName, DateTime sceneTimeOfCollection,
			String sceneId, Object extras, String planetApiKey) {
		this.jobId = jobId;
		this.jobName = jobName;
		this.status = status;
		this.createdByUserId = createdByUserId;
		this.createdOn = createdOn;
		this.algorithmName = algorithmName;
		this.algorithmVersion = algorithmVersion;
		this.geometry = geometry;
		this.sceneSensorName = sceneSensorName;
		this.sceneTimeOfCollection = sceneTimeOfCollection;
		this.sceneId = sceneId;
		this.extras = extras;
		this.planetApiKey = planetApiKey;
	}	

	/**
	 * @return the status
	 */
	public String getStatus() {
		return status;
	}

	/**
	 * @return the createdByUserId
	 */
	public String getCreatedByUserId() {
		return createdByUserId;
	}

	/**
	 * @return the createdOn
	 */
	public DateTime getCreatedOn() {
		return createdOn;
	}

	/**
	 * @return the algorithmName
	 */
	public String getAlgorithmName() {
		return algorithmName;
	}

	/**
	 * @return the algorithmVersion
	 */
	public String getAlgorithmVersion() {
		return algorithmVersion;
	}

	/**
	 * @return the geometry
	 */
	public Object getGeometry() {
		return geometry;
	}

	/**
	 * @return the sceneSensorName
	 */
	public String getSceneSensorName() {
		return sceneSensorName;
	}

	/**
	 * @return the sceneTimeOfCollection
	 */
	public DateTime getSceneTimeOfCollection() {
		return sceneTimeOfCollection;
	}

	/**
	 * @return the sceneId
	 */
	public String getSceneId() {
		return sceneId;
	}

	/**
	 * @return the extras
	 */
	public Object getExtras() {
		return extras;
	}

	/**
	 * @return the jobId
	 */
	public String getJobId() {
		return jobId;
	}

	/**
	 * @return the jobName
	 */
	public String getJobName() {
		return jobName;
	}

}
