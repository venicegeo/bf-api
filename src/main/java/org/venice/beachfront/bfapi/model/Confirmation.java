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

public class Confirmation {
	@JsonProperty("id") private String id;
	@JsonProperty("success") private boolean success;
	
	public Confirmation(String id, boolean success) {
		this.id = id;
		this.success = success;
	}
	
	public String getId() {
		return this.id;
	}
	
	public boolean getSuccess() {
		return this.success;
	}
}
