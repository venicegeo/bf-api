package org.venice.beachfront.bfapi.controllers;

import java.io.BufferedWriter;
import java.io.PrintWriter;
import java.io.StringWriter;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.venice.beachfront.bfapi.model.exception.UserException;

import model.logger.Severity;
import util.PiazzaLogger;

@ControllerAdvice
public class UserExceptionHandler {
	@Autowired
	private PiazzaLogger logger;
	
	@ExceptionHandler(UserException.class)
	public ResponseEntity<String> handleUserException(UserException ex) {
		String logMessage = String.format("[%d] %s -- %s", ex.getRecommendedStatusCode().value(), ex.getMessage(), ex.getDetails());
		this.logger.log(logMessage, Severity.ERROR);
		return ResponseEntity.status(ex.getRecommendedStatusCode())
				.contentType(MediaType.TEXT_PLAIN)
				.body(ex.getMessage());
	}
	
	@ExceptionHandler(RuntimeException.class)
	public ResponseEntity<String> handleRuntimeException(RuntimeException ex) {
		if (ex.getCause() != null && ex.getCause().getClass() == UserException.class) {
			return this.handleUserException((UserException)ex.getCause());
		}
		String logMessage = String.format("[500] Unknown runtime error -- %s", ex.getMessage());
		this.logger.log(logMessage, Severity.ERROR);
		
		StringWriter sw = new StringWriter();
		ex.printStackTrace(new PrintWriter(sw));
		this.logger.log(sw.toString(), Severity.ERROR);
		
		return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
			.contentType(MediaType.TEXT_PLAIN)
			.body(ex.getMessage());
	}
}
