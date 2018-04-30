package org.venice.beachfront.bfapi.config;

import java.util.Arrays;
import java.util.List;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;

import model.logger.Severity;
import util.PiazzaLogger;

@Configuration
public class CRSFConfig extends WebMvcConfigurerAdapter {
	@Value("${auth.allowedOrigins}")
	private String allowedOrigins;

	@Value("${auth.publicEndpoints}")
	private String publicEndpoints;

	@Autowired
	private PiazzaLogger piazzaLogger;

	@Override
	public void addInterceptors(InterceptorRegistry registry) {
		registry.addInterceptor(new HandlerInterceptorAdapter() {
			@Override
			public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
				// Allow OPTIONS for these purposes
				if ("OPTIONS".equals(request.getMethod())) {
					return true;
				}
				// Allow public endpoints
				if (isPublicEndpoint(request.getServletPath())) {
					return true;
				}
				final String origin = request.getHeader(HttpHeaders.ORIGIN);
				final String referer = request.getHeader(HttpHeaders.REFERER);
				final String requestedWith = request.getHeader("X-Requested-With");
				final String allowedRequestHeaders = request.getHeader(HttpHeaders.ACCESS_CONTROL_REQUEST_HEADERS);
				final boolean isAccessControlRequestHeader = (allowedRequestHeaders != null)
						? allowedRequestHeaders.contains("X-Requested-With") : false;
				final boolean isRequestXhr = "XMLHttpRequest".equals(requestedWith);
				final boolean isXhr = isRequestXhr || isAccessControlRequestHeader;

				if (isAllowedOrigin(origin) && isXhr) {
					// Allow cors request from approved endpoint
					return true;
				}

				if ((origin == null || origin.isEmpty()) && (referer == null || referer.isEmpty())) {
					// Allow non-CORS request
					return true;
				}

				piazzaLogger.log(String.format("Possible CSRF attempt: endpoint=`%s` origin=`%s` referrer=`%s` ip=`%s` is_xhr=`%s`",
						request.getServletPath(), origin, referer, request.getRemoteAddr(), isXhr), Severity.WARNING);
				response.sendError(HttpServletResponse.SC_FORBIDDEN, "Access Denied: CORS request validation failed");
				return false;
			}
		});
	}

	private boolean isAllowedOrigin(String origin) {
		final List<String> allowedOriginsList = Arrays.asList(allowedOrigins.split(","));
		return allowedOriginsList.stream().anyMatch(str -> str.trim().equals(origin));
	}

	private boolean isPublicEndpoint(String path) {
		final List<String> pubicEndpointsList = Arrays.asList(publicEndpoints.split(","));
		return pubicEndpointsList.stream().anyMatch(str -> str.trim().equals(path));
	}
}
