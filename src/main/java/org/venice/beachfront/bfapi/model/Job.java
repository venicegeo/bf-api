package org.venice.beachfront.bfapi.model;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.Transient;

import org.joda.time.DateTime;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import com.vividsolutions.jts.geom.Geometry;

@Entity
@Table(name = "__beachfront__job")
public class Job {
	@Id
	@JsonProperty("job_id")
	private String jobId;
	@JsonProperty("name")
	private String jobName;
	@JsonProperty("status")
	private String status;
	@JsonProperty("created_by")
	private String createdByUserId;
	@JsonProperty("created_on")
	private DateTime createdOn;
	@JsonProperty("algorithm_name")
	private String algorithmName;
	@JsonProperty("algorithm_version")
	private String algorithmVersion;
	@JsonProperty("geometry")
	@Transient
	private Geometry geometry;
	@JsonProperty("scene_sensor_name")
	private String sceneSensorName;
	@JsonProperty("scene_time_of_collect")
	private DateTime sceneTimeOfCollection;
	@JsonProperty("scene_id")
	private String sceneId;
	@JsonProperty("tide")
	private double tide;
	@JsonProperty("tide_min_24h")
	private double tideMin24h;
	@JsonProperty("tide_max_24h")
	private double tideMax24h;
	@JsonProperty("extras")
	@Transient
	private JsonNode extras;
	@JsonProperty("compute_mask")
	private Boolean computeMask;
	@JsonIgnore
	private String planetApiKey;

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
	 * @param algorithmName
	 *            name (ID) of algorithm job is using
	 * @param algorithmVersion
	 *            version of algorithm job is using
	 * @param geometry
	 *            GeoJSON geometry describing the job
	 * @param sceneSensorName
	 *            name of sensor source for job imagery
	 * @param sceneTimeOfCollection
	 *            collection time of job imagery
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
	 * @param planetApiKey
	 *            API key to use when contacting the Planet Labs API
	 */
	public Job(String jobId, String jobName, String status, String createdByUserId, DateTime createdOn, String algorithmName,
			String algorithmVersion, Geometry geometry, String sceneSensorName, DateTime sceneTimeOfCollection, String sceneId,
			double tide, double tideMin24h, double tideMax24h, JsonNode extras, Boolean computeMask, String planetApiKey) {
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
		this.tide = tide;
		this.tideMin24h = tideMin24h;
		this.tideMax24h = tideMax24h;
		this.extras = extras;
		this.computeMask = computeMask;
		this.planetApiKey = planetApiKey;
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

	public Geometry getGeometry() {
		return geometry;
	}

	public void setGeometry(Geometry geometry) {
		this.geometry = geometry;
	}

	public String getSceneSensorName() {
		return sceneSensorName;
	}

	public void setSceneSensorName(String sceneSensorName) {
		this.sceneSensorName = sceneSensorName;
	}

	public DateTime getSceneTimeOfCollection() {
		return sceneTimeOfCollection;
	}

	public void setSceneTimeOfCollection(DateTime sceneTimeOfCollection) {
		this.sceneTimeOfCollection = sceneTimeOfCollection;
	}

	public String getSceneId() {
		return sceneId;
	}

	public void setSceneId(String sceneId) {
		this.sceneId = sceneId;
	}

	public double getTide() { return tide; }

	public void setTide(double tide) {
		this.tide = tide;
	}

	public double getTideMin24h() { return tideMin24h; }

	public void setTideMin24h(double tideMin24h) {
		this.tideMin24h = tideMin24h;
	}

	public double getTideMax24h() { return tideMax24h; }

	public void setTideMax24h(double tideMax24h) {
		this.tideMax24h = tideMax24h;
	}

	public JsonNode getExtras() {
		return extras;
	}

	public void setExtras(JsonNode extras) {
		this.extras = extras;
	}

	public String getPlanetApiKey() {
		return planetApiKey;
	}

	public void setPlanetApiKey(String planetApiKey) {
		this.planetApiKey = planetApiKey;
	}

	/**
	 * @return the computeMask
	 */
	public Boolean getComputeMask() {
		return computeMask;
	}

}
