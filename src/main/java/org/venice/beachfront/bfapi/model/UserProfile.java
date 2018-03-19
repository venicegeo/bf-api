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

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.converter.TimestampConverter;

import com.fasterxml.jackson.annotation.JsonProperty;

import io.swagger.annotations.ApiModelProperty;

@Entity
@Table(name = "__beachfront__user")
public class UserProfile {
	@Id
	@Column(name = "user_id")
	@JsonProperty("user_id")
	@ApiModelProperty(required = true, value = "Unique ID of the user")
	private String userId;
	@Column(name = "user_name")
	@JsonProperty("user_name")
	@ApiModelProperty(required = true, value = "Display name of the user")
	private String name;
	@Column(name = "api_key")
	@JsonProperty("api_key")
	@ApiModelProperty(required = true, value = "The API Key used for service interaction")
	private String apiKey;
	@Convert(converter = TimestampConverter.class)
	@Column(name = "created_on")
	@JsonProperty("created_on")
	@ApiModelProperty(required = true, value = "The time the user profile was first created")
	private DateTime createdOn;
	@Convert(converter = TimestampConverter.class)
	@Column(name = "last_accessed")
	@JsonProperty("last_accessed")
	@ApiModelProperty(required = true, value = "The time the user profile was last used to access services")
	private DateTime lastAccessed;

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
		this.lastAccessed = createdOn; // First instance of access
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

	public DateTime getLastAccessed() {
		return lastAccessed;
	}

	public void setLastAccessed(DateTime lastAccessed) {
		this.lastAccessed = lastAccessed;
	}

}
