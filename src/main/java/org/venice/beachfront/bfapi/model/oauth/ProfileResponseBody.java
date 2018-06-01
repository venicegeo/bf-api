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
	private AbstractStringList commonName;

	@JsonProperty(value = "memberof", required = false)
	private AbstractStringList memberOf;

	@JsonProperty(value = "firstname", required = false)
	private String firstname;

	@JsonProperty(value = "lastname", required = false)
	private String lastname;

	@JsonProperty(value = "ID", required = false)
	private String id;

	public ProfileResponseBody() {
		super();
	}

	public ProfileResponseBody(String dn, AbstractStringList commonName, AbstractStringList memberOf, String firstname, String lastname, String id) {
		this.dn = dn;
		this.commonName = commonName;
		this.memberOf = memberOf;
		this.firstname = firstname;
		this.lastname = lastname;
		this.id = id;
	}

	public String getDn() {
		return dn;
	}

	public AbstractStringList getCommonName() {
		return commonName;
	}

	public AbstractStringList getMemberOf() {
		return memberOf;
	}

	public String getFirstname() { return firstname; }

	public String getLastname() { return lastname; }

	public String getId() { return id; }

	public String getComputedUserId() throws UserException {
		if (this.dn != null && this.dn.length() > 0) {
			return this.dn;
		}
		if (this.commonName != null && this.commonName.toString().length() > 0 && this.memberOf != null && this.memberOf.toString().length() > 0) {
			return String.format("%s@%s", this.commonName.toString(), this.memberOf);
		}
		if (this.firstname != null && this.firstname.length() > 0 &&
				this.lastname != null && this.lastname.length() > 0 &&
				this.id != null && this.id.length() > 0) {
			// This user is an ID.me user
			return String.format("%s@%s-%s", this.id, this.lastname, this.firstname);
		}
		throw new UserException("Could not obtain a user ID from OAuth profile response", this.toString(),
				HttpStatus.INTERNAL_SERVER_ERROR);
	}

	public String getComputedUserName() throws UserException {
		if (this.commonName != null && this.commonName.toString().length() > 0) {
			return this.commonName.toString();
		}
		if (this.id != null && this.id.length() > 0) {
			return this.id;
		}
		throw new UserException("Could not obtain a user name from OAuth profile response", this.toString(),
				HttpStatus.INTERNAL_SERVER_ERROR);
	}

	public void validate() throws UserException {
		getComputedUserId();
		getComputedUserName();
	}
}
