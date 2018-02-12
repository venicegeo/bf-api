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
	@Transient
	private HttpStatus recommendedStatusCode;

	public UserException() {

	}

	public UserException(String message, String details, HttpStatus recommendedStatusCode) {
		this.message = message;
		this.details = details;
		this.recommendedStatusCode = recommendedStatusCode;
	}
}
