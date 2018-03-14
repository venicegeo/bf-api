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
package org.venice.beachfront.bfapi.model.oauth;

import org.springframework.http.HttpStatus;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class ProfileResponseBody {
	@JsonProperty(value = "DN", required = false)
	private String dn;

	@JsonProperty(value = "commonname", required = false)
	private String commonName;

	@JsonProperty(value = "memberof", required = false)
	private String memberOf;

	public ProfileResponseBody() {
		super();
	}

	public ProfileResponseBody(String dn, String commonName, String memberOf) {
		this.dn = dn;
		this.commonName = commonName;
		this.memberOf = memberOf;
	}

	public String getDn() {
		return dn;
	}

	public String getCommonName() {
		return commonName;
	}

	public String getMemberOf() {
		return memberOf;
	}

	public String getComputedUserId() throws UserException {
		if (this.dn != null && this.dn.length() > 0) {
			return this.dn;
		}
		if (this.commonName != null && this.commonName.length() > 0 && this.memberOf != null && this.memberOf.length() > 0) {
			return String.format("%s@%s", this.commonName, this.memberOf);
		}
		throw new UserException("Could not obtain a user ID from OAuth profile response", this.toString(),
				HttpStatus.INTERNAL_SERVER_ERROR);
	}

	public String getComputedUserName() throws UserException {
		if (this.commonName != null && this.commonName.length() > 0) {
			return this.commonName;
		}
		throw new UserException("Could not obtain a user name from OAuth profile response", this.commonName,
				HttpStatus.INTERNAL_SERVER_ERROR);
	}

}
