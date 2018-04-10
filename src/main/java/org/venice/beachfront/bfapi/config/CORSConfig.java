package org.venice.beachfront.bfapi.config;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;

/**
 * Ensures proper CORS headers are present in all requests
 */
@Configuration
public class CORSConfig extends WebMvcConfigurerAdapter {

	@Value("${DOMAIN}")
	private String domain;

	@Override
	public void addInterceptors(InterceptorRegistry registry) {
		registry.addInterceptor(new HandlerInterceptorAdapter() {
			@Override
			public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
				response.setHeader("Access-Control-Allow-Headers", "authorization, content-type, X-Requested-With");
				response.setHeader("Access-Control-Allow-Origin", "https://beachfront." + domain);
				response.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
				response.setHeader("Access-Control-Max-Age", "36000");
				return true;
			}
		});
	}
}