/**
 * 
 */
package org.venice.beachfront.bfapi.services;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.Enumeration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.function.Supplier;

import javax.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.model.Environment;

/**
 * @author fsufitch
 *
 */
public class IABrokerPassthroughServiceImpl implements IABrokerPassthroughService {

	@Autowired private Environment env;
	@Autowired private ExecutorService executorService;

	@Override
	public CompletableFuture<Response> passthroughRequest(String uri, HttpServletRequest request) throws MalformedURLException, IOException {
		URL ptUrl = this.getIABrokerURL(uri);
		HttpMethod method = HttpMethod.valueOf(request.getMethod());
		HttpHeaders headers = this.getHeaders(request);
		char[] content = this.getContent(request);

		IABrokerPassthroughServiceImpl this_ = this;
		Supplier<IABrokerPassthroughService.Response> asyncResponseSupplier = new Supplier<IABrokerPassthroughService.Response>(){
			public IABrokerPassthroughService.Response get() {
				try {
					return this_.getPassthroughResponse(method, ptUrl, headers, content);
				} catch (Exception e) {
					throw new RuntimeException(e);
				}

			}
		};


		return CompletableFuture.supplyAsync(asyncResponseSupplier, this.executorService);

	}

	private URL getIABrokerURL(String uri) throws MalformedURLException {
		return new URL(this.env.getIABrokerBaseUrl(), uri);
	}

	private HttpHeaders getHeaders(HttpServletRequest request) {
		HttpHeaders headers = new HttpHeaders();
		Enumeration<String> hNames = request.getHeaderNames();
		while (hNames.hasMoreElements()) {
			String hName = hNames.nextElement();
			headers.add(hName, request.getHeader(hName));
		}
		
		if (headers.containsKey("x-forwarded-for")) {
			headers.set("x-forwarded-for", headers.getFirst("x-forwarded-for") + ", " + request.getRemoteAddr());
		} else {
			headers.set("x-forwarded-for", request.getRemoteAddr());			
		}
		
		return headers;
	}

	private char[] getContent(HttpServletRequest request) throws IOException{
		char[] content = new char[0];
		if (request.getContentLength() > 0) {
			content = new char[request.getContentLength()];
			request.getReader().read(content);
		}
		return content;
	}

	private IABrokerPassthroughService.Response getPassthroughResponse(HttpMethod method, URL url, HttpHeaders headers, char[] content) {
		HttpStatus responseCode;
		HttpHeaders responseHeaders = new HttpHeaders();
		byte[] responseContent = new byte[0];

		HttpEntity<char[]> entity = new HttpEntity<char[]>(content, headers);
		try {
			ResponseEntity<String> response = new RestTemplate().exchange(url.toString(), method, entity, String.class);
	
			responseCode = response.getStatusCode();
			responseHeaders = response.getHeaders();
			responseContent = response.getBody().getBytes();
		} catch (HttpClientErrorException | HttpServerErrorException e) {
			responseCode = e.getStatusCode();
			responseHeaders = e.getResponseHeaders();
			responseContent = e.getResponseBodyAsByteArray();
		} catch (RestClientException e) {
			responseCode = HttpStatus.INTERNAL_SERVER_ERROR;
			responseContent = e.toString().getBytes();
		}

		return this.createResponse(responseCode, responseHeaders, responseContent);
	}

	private IABrokerPassthroughService.Response createResponse(HttpStatus responseCode, HttpHeaders responseHeaders, byte[] responseContent) {
		return new IABrokerPassthroughService.Response() {
			public byte[] getBody() {
				return responseContent;
			}

			public HttpStatus getStatusCode() {
				return responseCode;
			}

			public HttpHeaders getHeaders() {
				return responseHeaders;
			}
		};
	}
}
