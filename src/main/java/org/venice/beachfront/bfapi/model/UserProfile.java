package org.venice.beachfront.bfapi.model;

import javax.persistence.Column;
import javax.persistence.Convert;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.converter.TimestampConverter;

import com.fasterxml.jackson.annotation.JsonProperty;

@Entity
@Table(name = "__beachfront__user")
public class UserProfile {
	@Id
	@Column(name = "user_id")
	@JsonProperty("user_id")
	private String userId;
	@Column(name = "user_name")
	@JsonProperty("user_name")
	private String name;
	@Column(name = "api_key")
	@JsonProperty("api_key")
	private String apiKey;
	@Convert(converter = TimestampConverter.class)
	@Column(name = "created_on")
	@JsonProperty("created_on")
	private DateTime createdOn;

	/**
	 * Default constructor for Hibernate.
	 */
	public UserProfile() {
		super();
	}

	public UserProfile(String user_id, String name, String apiKey, DateTime createdOn) {
		this.userId = user_id;
		this.name = name;
		this.apiKey = apiKey;
		this.createdOn = createdOn;
	}

	public String getUserId() {
		return userId;
	}

	public void setUserId(String userId) {
		this.userId = userId;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public String getApiKey() {
		return apiKey;
	}

	public void setApiKey(String apiKey) {
		this.apiKey = apiKey;
	}

	public DateTime getCreatedOn() {
		return createdOn;
	}

	public void setCreatedOn(DateTime createdOn) {
		this.createdOn = createdOn;
	}

}
