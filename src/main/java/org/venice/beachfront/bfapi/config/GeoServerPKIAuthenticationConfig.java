package org.venice.beachfront.bfapi.config;

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
import java.util.List;

import javax.net.ssl.SSLContext;

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
import org.apache.http.protocol.HttpContext;
import org.apache.http.ssl.SSLContexts;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.http.converter.FormHttpMessageConverter;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.geoserver.AuthHeaders;
import org.venice.beachfront.bfapi.geoserver.PKIAuthHeaders;

/**
 * Configures the API to use PKI authentication when communicating with GeoServer
 */
@Configuration
@Profile({ "pki-geoserver-auth" })
public class GeoServerPKIAuthenticationConfig extends GeoServerBaseAuthenticationConfig {

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
	public HttpClient httpClient() throws KeyManagementException, UnrecoverableKeyException, NoSuchAlgorithmException, 
		KeyStoreException, CertificateException, IOException {

		final SSLContext sslContext = SSLContexts.custom().loadKeyMaterial(getStore(), piazzaKeyPassphrase.toCharArray())
				.loadTrustMaterial(null, new TrustSelfSignedStrategy()).useProtocol("TLS").build();
		final Registry<CookieSpecProvider> registry = RegistryBuilder.<CookieSpecProvider>create()
				.register("myspec", new MySpecProvider()).build();
		final RequestConfig requestConfig = RequestConfig.custom().setCookieSpec("myspec").setCircularRedirectsAllowed(true).build();

		// @formatter:off
		return HttpClientBuilder.create()
				.setDefaultRequestConfig(requestConfig)
				.setMaxConnTotal(httpMaxTotal)
				.setSSLContext(sslContext)
				.setSSLHostnameVerifier(new NoopHostnameVerifier())
				.setDefaultCookieStore(new BasicCookieStore())
				.setDefaultCookieSpecRegistry(registry)
				.setRedirectStrategy(new MyRedirectStrategy())
				.setMaxConnPerRoute(httpMaxRoute)
				.setKeepAliveStrategy(getKeepAliveStrategy())
				.build();
		// @formatter:on
	}

	@Bean
	public RestTemplate restTemplate(@Autowired HttpClient httpClient) {
		final RestTemplate restTemplate = new RestTemplate();
		restTemplate.setRequestFactory(new HttpComponentsClientHttpRequestFactory(httpClient));

		final List<HttpMessageConverter<?>> messageConverters = new ArrayList<>();
		messageConverters.add(new StringHttpMessageConverter());
		messageConverters.add(new MappingJackson2HttpMessageConverter());
		messageConverters.add(new FormHttpMessageConverter());

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