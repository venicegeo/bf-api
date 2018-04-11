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
package org.venice.beachfront.bfapi;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.security.KeyManagementException;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.UnrecoverableKeyException;
import java.security.cert.CertificateException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.net.ssl.SSLContext;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.http.HeaderElement;
import org.apache.http.HeaderElementIterator;
import org.apache.http.HttpRequest;
import org.apache.http.HttpResponse;
import org.apache.http.HttpStatus;
import org.apache.http.ProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpHead;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.client.methods.RequestBuilder;
import org.apache.http.config.Registry;
import org.apache.http.config.RegistryBuilder;
import org.apache.http.conn.ConnectionKeepAliveStrategy;
import org.apache.http.conn.ssl.NoopHostnameVerifier;
import org.apache.http.conn.ssl.TrustSelfSignedStrategy;
import org.apache.http.cookie.Cookie;
import org.apache.http.cookie.CookieOrigin;
import org.apache.http.cookie.CookieSpec;
import org.apache.http.cookie.CookieSpecProvider;
import org.apache.http.cookie.MalformedCookieException;
import org.apache.http.impl.client.BasicCookieStore;
import org.apache.http.impl.client.DefaultRedirectStrategy;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.impl.cookie.DefaultCookieSpec;
import org.apache.http.message.BasicHeaderElementIterator;
import org.apache.http.protocol.HTTP;
import org.apache.http.protocol.HttpContext;
import org.apache.http.ssl.SSLContexts;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.security.authentication.AuthenticationDetailsSource;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.Authentication;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;
import org.venice.beachfront.bfapi.auth.ApiKeyAuthProvider;
import org.venice.beachfront.bfapi.auth.ExtendedRequestDetails;
import org.venice.beachfront.bfapi.auth.FailedAuthEntryPoint;
import org.venice.beachfront.bfapi.geoserver.AuthHeaders;
import org.venice.beachfront.bfapi.geoserver.BasicAuthHeaders;
import org.venice.beachfront.bfapi.geoserver.PKIAuthHeaders;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.joda.JodaModule;

import io.swagger.annotations.ApiOperation;
import model.logger.Severity;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import util.PiazzaLogger;

@Configuration
public class BfApiConfig {
	@Value("${http.keep.alive.duration.seconds}")
	private int httpKeepAliveDurationSeconds;

	@Bean
	public ObjectMapper getJacksonObjectMapper() {
		ObjectMapper mapper = new ObjectMapper();
		mapper.registerModule(new JodaModule());
		return mapper;
	}

	@Bean
	public ExecutorService getExecutor(@Value("${concurrent.threads}") int threads) {
		return Executors.newFixedThreadPool(threads);
	}

	/**
	 * Ensures proper CORS headers are present in all requests
	 */
	@Configuration
	protected static class AddCorsHeaders extends WebMvcConfigurerAdapter {
		@Value("${DOMAIN}")
		private String domain;

		@Value("${auth.allowedOrigins}")
		private String allowedOrigins;

		@Override
		public void addInterceptors(InterceptorRegistry registry) {
			registry.addInterceptor(new HandlerInterceptorAdapter() {
				@Override
				public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
					final String origin = request.getHeader("Origin");
					final List<String> allowedOriginsList = Arrays.asList(allowedOrigins.split(","));
					final boolean isAllowed = allowedOriginsList.stream().anyMatch(str -> str.trim().equals(origin));
					if (isAllowed) {
						response.setHeader("Access-Control-Allow-Origin", origin);
					}
					response.setHeader("Access-Control-Allow-Headers", "authorization, content-type, X-Requested-With");
					response.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
					response.setHeader("Access-Control-Allow-Credentials", "true");
					response.setHeader("Access-Control-Max-Age", "36000");
					return true;
				}
			});
		}
	}

	/**
	 * Ensures proper CORS headers are present in all requests
	 */
	@Configuration
	protected static class AddCrsfFilter extends WebMvcConfigurerAdapter {
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

	/**
	 * Initializes the security providers for validating API Keys on all requests that require API Key validation.
	 */
	@Configuration
	protected static class ApplicationSecurity extends WebSecurityConfigurerAdapter {
		@Autowired
		private ApiKeyAuthProvider apiKeyAuthProvider;
		@Autowired
		private FailedAuthEntryPoint failureEntryPoint;

		@Override
		public void configure(HttpSecurity http) throws Exception {
			http.authorizeRequests().antMatchers(HttpMethod.OPTIONS).permitAll() // Allow any OPTIONS for REST best
																					// practices
					.antMatchers("/").permitAll() // Allow unauthenticated queries to root (health check) path
					.antMatchers("/oauth/callback").permitAll() // Allow unauthenticated queries to login callback path
					.antMatchers("/oauth/start").permitAll() // Allow unauthenticated queries to OAuth login start path
					.antMatchers("/v2/api-docs").permitAll() // Allow unauthenticated queries for Swagger documentation
					.anyRequest().authenticated() // All other requests must be authenticated
					.and().httpBasic() // Use HTTP Basic authentication
					.authenticationEntryPoint(this.failureEntryPoint) // Entry point for starting a Basic auth exchange
																		// (i.e. "failed authentication" handling)
					.authenticationDetailsSource(this.authenticationDetailsSource()) // Feed more request details into
																						// any providers
					.and().sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS) // Do not create
																										// or manage
																										// sessions for
																										// security
					.and().logout().disable() // Disable auto-magical Spring Security logout behavior
					.authenticationProvider(this.apiKeyAuthProvider) // Use this custom authentication provider to
																		// authenticate requests
					.csrf().disable(); // Disable advanced CSRF protections for better statelessness
		}

		private AuthenticationDetailsSource<HttpServletRequest, ExtendedRequestDetails> authenticationDetailsSource() {
			return new AuthenticationDetailsSource<HttpServletRequest, ExtendedRequestDetails>() {
				@Override
				public ExtendedRequestDetails buildDetails(HttpServletRequest request) {
					return new ExtendedRequestDetails(request);
				}
			};
		}
	}

	/**
	 * Configures the API to use basic HTTP authentication when communicating with GeoServer
	 */
	@Profile({ "basic-geoserver-auth" })
	protected class BasicAuthenticationConfig {

		@Value("${http.max.total}")
		private int httpMaxTotal;

		@Value("${http.max.route}")
		private int httpMaxRoute;

		@Bean
		public RestTemplate restTemplate() {
			final RestTemplate restTemplate = new RestTemplate();
			final HttpClient httpClient = HttpClientBuilder.create().setMaxConnTotal(httpMaxTotal).setMaxConnPerRoute(httpMaxRoute)
					.setSSLHostnameVerifier(new NoopHostnameVerifier()).setKeepAliveStrategy(getKeepAliveStrategy()).build();
			restTemplate.setRequestFactory(new HttpComponentsClientHttpRequestFactory(httpClient));
			return restTemplate;
		}

		@Bean
		public AuthHeaders authHeaders() {
			return new BasicAuthHeaders();
		}
	}

	/**
	 * Configures the API to use PKI authentication when communicating with GeoServer
	 */
	@Configuration
	@Profile({ "pki-geoserver-auth" })
	protected class PKIAuthenticationConfig {
		@Value("${http.max.total}")
		private int httpMaxTotal;
		@Value("${http.max.route}")
		private int httpMaxRoute;
		@Value("${JKS_FILE}")
		private String keystoreFileName;
		@Value("${JKS_PASSPHRASE}")
		private String keystorePassphrase;
		@Value("${PZ_PASSPHRASE}")
		private String piazzaKeyPassphrase;

		@Bean
		public RestTemplate restTemplate() throws KeyManagementException, UnrecoverableKeyException, NoSuchAlgorithmException,
				KeyStoreException, CertificateException, IOException {
			final SSLContext sslContext = SSLContexts.custom().loadKeyMaterial(getStore(), piazzaKeyPassphrase.toCharArray())
					.loadTrustMaterial(null, new TrustSelfSignedStrategy()).useProtocol("TLS").build();
			final Registry<CookieSpecProvider> registry = RegistryBuilder.<CookieSpecProvider>create()
					.register("myspec", new MySpecProvider()).build();
			final RequestConfig requestConfig = RequestConfig.custom().setCookieSpec("myspec").setCircularRedirectsAllowed(true).build();
			final HttpClient httpClient = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).setMaxConnTotal(httpMaxTotal)
					.setSSLContext(sslContext).setSSLHostnameVerifier(new NoopHostnameVerifier())
					.setDefaultCookieStore(new BasicCookieStore()).setDefaultCookieSpecRegistry(registry)
					.setRedirectStrategy(new MyRedirectStrategy()).setMaxConnPerRoute(httpMaxRoute)
					.setKeepAliveStrategy(getKeepAliveStrategy()).build();
			final RestTemplate restTemplate = new RestTemplate();
			restTemplate.setRequestFactory(new HttpComponentsClientHttpRequestFactory(httpClient));
			final List<HttpMessageConverter<?>> messageConverters = new ArrayList<HttpMessageConverter<?>>();
			messageConverters.add(new StringHttpMessageConverter());
			messageConverters.add(new MappingJackson2HttpMessageConverter());
			restTemplate.setMessageConverters(messageConverters);
			return restTemplate;
		}

		@Bean
		public AuthHeaders authHeaders() {
			return new PKIAuthHeaders();
		}

		protected KeyStore getStore() throws KeyStoreException, IOException, CertificateException, NoSuchAlgorithmException {
			final KeyStore store = KeyStore.getInstance(KeyStore.getDefaultType());
			try (final InputStream inputStream = getClass().getClassLoader().getResourceAsStream(keystoreFileName)) {
				store.load(inputStream, keystorePassphrase.toCharArray());
			}
			return store;
		}

		protected class MyCookieSpec extends DefaultCookieSpec {
			@Override
			public void validate(Cookie c, CookieOrigin co) throws MalformedCookieException {
				// Do nothing; accept all cookies
			}
		}

		protected class MySpecProvider implements CookieSpecProvider {
			@Override
			public CookieSpec create(HttpContext context) {
				return new MyCookieSpec();
			}
		}

		protected class MyRedirectStrategy extends DefaultRedirectStrategy {
			@Override
			protected boolean isRedirectable(final String method) {
				return true;
			}

			@Override
			public HttpUriRequest getRedirect(final HttpRequest request, final HttpResponse response, final HttpContext context)
					throws ProtocolException {
				final URI uri = getLocationURI(request, response, context);
				final String method = request.getRequestLine().getMethod();

				if (method.equalsIgnoreCase(HttpHead.METHOD_NAME)) {
					return new HttpHead(uri);
				} else if (method.equalsIgnoreCase(HttpGet.METHOD_NAME)) {
					return new HttpGet(uri);
				} else {
					final int status = response.getStatusLine().getStatusCode();
					if (status == HttpStatus.SC_TEMPORARY_REDIRECT || status == HttpStatus.SC_MOVED_PERMANENTLY
							|| status == HttpStatus.SC_MOVED_TEMPORARILY) {
						return RequestBuilder.copy(request).setUri(uri).build();
					} else {
						return new HttpGet(uri);
					}
				}
			}
		}
	}

	/**
	 * Defines a keep-alive strategy for requests that do not provide a proper timeout value. This will avoid a case
	 * where keep-alive is set to permanent (when the header is missing) in cases where this application's environment
	 * will not allow for permanent connections.
	 */
	private ConnectionKeepAliveStrategy getKeepAliveStrategy() {
		// Returns the keep alive duration, in milliseconds
		return (HttpResponse response, HttpContext context) -> {
			HeaderElementIterator it = new BasicHeaderElementIterator(response.headerIterator(HTTP.CONN_KEEP_ALIVE));
			while (it.hasNext()) {
				final HeaderElement headerElement = it.nextElement();
				final String param = headerElement.getName();
				final String value = headerElement.getValue();
				if (value != null && param.equalsIgnoreCase("timeout")) {
					return Long.parseLong(value) * 1000;
				}
			}
			return httpKeepAliveDurationSeconds * 1000;
		};
	}

	@Bean
	public Docket beachfrontApi() {
		ApiInfo apiInfo = new ApiInfoBuilder().title("Beachfront API").description("Beachfront Web Services")
				.contact(new Contact("The VeniceGeo Project", "http://radiantblue.com", "venice@radiantblue.com")).version("0.1.0").build();
		return new Docket(DocumentationType.SWAGGER_2).useDefaultResponseMessages(false).ignoredParameterTypes(Authentication.class)
				.groupName("Beachfront").apiInfo(apiInfo).select().apis(RequestHandlerSelectors.withMethodAnnotation(ApiOperation.class)).paths(PathSelectors.any()).build();
	}

}