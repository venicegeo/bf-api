package org.venice.beachfront.bfapi.services;

import java.io.IOException;
import java.net.MalformedURLException;
import java.util.concurrent.CompletableFuture;

import javax.servlet.http.HttpServletRequest;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;

public interface IABrokerPassthroughService {
	public interface Response {
		public HttpStatus getStatusCode();
		public HttpHeaders getHeaders();
		public byte[] getBody();
	}

	public CompletableFuture<Response> passthroughRequest(String uri, HttpServletRequest request) throws MalformedURLException, IOException;
}
