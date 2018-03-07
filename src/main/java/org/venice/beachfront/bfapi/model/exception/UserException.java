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
package org.venice.beachfront.bfapi.model.exception;

import javax.persistence.Transient;

import org.springframework.http.HttpStatus;

/**
 * Intended to provide a sanitized User-facing exception that can be delivered through the REST Controllers back to the
 * user for display in the interface.
 */
public class UserException extends Exception {
	private static final long serialVersionUID = 1L;

	private String message;
	private String details;
	private Throwable cause;
	@Transient
	private HttpStatus recommendedStatusCode;

	public UserException(String message, HttpStatus recommendedStatusCode) {
		this.message = message;
		this.details = "";
		this.cause = null;
		this.recommendedStatusCode = recommendedStatusCode;
	}

	public UserException(String message, String details, HttpStatus recommendedStatusCode) {
		this.message = message;
		this.details = details;
		this.cause = null;
		this.recommendedStatusCode = recommendedStatusCode;
	}
	
	public UserException(String message, Throwable cause, HttpStatus recommendedStatusCode) {
		this.message = message;
		this.cause = cause;
		this.details = "";
		this.recommendedStatusCode = recommendedStatusCode;
	}

	public UserException(String message, Throwable cause, String details, HttpStatus recommendedStatusCode) {
		this.message = message;
		this.cause = cause;
		this.details = details;
		this.recommendedStatusCode = recommendedStatusCode;
	}

	@Override
	public String getMessage() {
		return message;
	}

	public String getDetails() {
		return details;
	}

	public HttpStatus getRecommendedStatusCode() {
		return recommendedStatusCode;
	}
	
	@Override
	public Throwable getCause() {
		return cause;
	}
}
