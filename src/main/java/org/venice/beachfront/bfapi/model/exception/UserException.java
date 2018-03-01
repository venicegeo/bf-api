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
