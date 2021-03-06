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

import com.fasterxml.jackson.annotation.JsonProperty;

import io.swagger.annotations.ApiModelProperty;

public class Algorithm {
	@JsonProperty("description")
	@ApiModelProperty(required = true, value = "description of the Algorithm function")
	private final String description;
	@JsonProperty("interface")
	@ApiModelProperty(required = true, value = "unique name of the Algorithm")
	private final String interface_;
	@JsonProperty("max_cloud_cover")
	@ApiModelProperty(required = true, value = "The maximum percentage of cloud cover acceptable to this Algorithm")
	private final int maxCloudCover;
	@JsonProperty("name")
	@ApiModelProperty(required = true, value = "friendly name for this Algorithm")
	private final String name;
	@JsonProperty("service_id")
	@ApiModelProperty(required = true, value = "The unique ID of the Algorithm as registed as a Piazza service")
	private final String serviceId;
	@JsonProperty("version")
	@ApiModelProperty(required = true, value = "current version of this Algorithm")
	private final String version;

	/**
	 * @param description
	 * @param interface_
	 * @param maxCloudCover
	 * @param name
	 * @param serviceId
	 * @param version
	 */
	public Algorithm(String description, String interface_, int maxCloudCover, String name, String serviceId, String version) {
		this.description = description;
		this.interface_ = interface_;
		this.maxCloudCover = maxCloudCover;
		this.name = name;
		this.serviceId = serviceId;
		this.version = version;
	}

	public String getDescription() {
		return description;
	}

	public String getInterface() {
		return interface_;
	}

	public int getMaxCloudCover() {
		return maxCloudCover;
	}

	public String getName() {
		return name;
	}

	public String getServiceId() {
		return serviceId;
	}

	public String getVersion() {
		return version;
	}
}
