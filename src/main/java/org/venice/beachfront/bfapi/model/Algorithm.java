package org.venice.beachfront.bfapi.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class Algorithm {
	@JsonProperty("description") private final String description;
	@JsonProperty("interface") private final String interface_;
	@JsonProperty("max_cloud_cover") private final int maxCloudCover;
	@JsonProperty("name") private final String name;
	@JsonProperty("service_id") private final String serviceId;
	@JsonProperty("version") private final String version;

	/**
	 * @param description
	 * @param interface_
	 * @param maxCloudCover
	 * @param name
	 * @param serviceId
	 * @param version
	 */
	public Algorithm(String description, String interface_, int maxCloudCover, String name, String serviceId,
			String version) {
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
