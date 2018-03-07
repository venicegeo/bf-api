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
import javax.persistence.EmbeddedId;
import javax.persistence.Entity;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.vividsolutions.jts.geom.Geometry;

@Entity
@Table(name = "__beachfront__detection")
public class Detection {
	@EmbeddedId
	private DetectionPK detectionPK;
	@Column(name = "geometry")
	@JsonProperty("geometry")
	private Geometry geometry;

	public Detection() {

	}

	public Detection(Job job, int featureId, Geometry geometry) {
		this.detectionPK = new DetectionPK(job, featureId);
		this.geometry = geometry;
	}

	public DetectionPK getDetectionPK() {
		return detectionPK;
	}

	public void setDetectionPK(DetectionPK detectionPK) {
		this.detectionPK = detectionPK;
	}

	public Geometry getGeometry() {
		return geometry;
	}

	public void setGeometry(Geometry geometry) {
		this.geometry = geometry;
	}
}
