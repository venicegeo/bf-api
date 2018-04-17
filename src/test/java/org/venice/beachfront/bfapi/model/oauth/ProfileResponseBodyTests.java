package org.venice.beachfront.bfapi.model.oauth;

import java.io.File;
import java.io.IOException;

import org.apache.commons.io.IOUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.module.SimpleModule;

public class ProfileResponseBodyTests {
	private ObjectMapper objectMapper;
	
	@Before
	public void setup() {
		ObjectMapper mapper = new ObjectMapper();
		SimpleModule module = new SimpleModule();
		module.addDeserializer(GeoAxisCommonName.class, new GeoAxisCommonName.Deserializer());
		mapper.registerModule(module);
		this.objectMapper = mapper;
	}
	
	
	@Test
	public void testParseSingleCNGeoAxisBody() throws IOException {
		// Mock
		String responseJson = IOUtils.toString(
				this.getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "model", File.separator, "geoaxis-single-cn.json")),
				"UTF-8");
		
		// Test
		ProfileResponseBody body = objectMapper.readValue(responseJson, ProfileResponseBody.class);
		
		// Asserts
		Assert.assertEquals("distinguished-name.test.localdomain", body.getDn());
		Assert.assertEquals("testuser.localdomain", body.getCommonName().toString());
		Assert.assertEquals("testorg.localdomain", body.getMemberOf());
		Assert.assertEquals("FirstName", body.getFirstname());
		Assert.assertEquals("LastName", body.getLastname());
		Assert.assertEquals("test-id-123", body.getId());
	}

	@Test
	public void testParseMultiCNGeoAxisBody() throws IOException {
		// Mock
		String responseJson = IOUtils.toString(
				this.getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "model", File.separator, "geoaxis-multi-cn.json")),
				"UTF-8");
		
		// Test
		ProfileResponseBody body = objectMapper.readValue(responseJson, ProfileResponseBody.class);
		
		// Asserts
		Assert.assertEquals("distinguished-name.test.localdomain", body.getDn());
		Assert.assertEquals("testuser1.localdomain", body.getCommonName().toString());
		Assert.assertEquals("testorg.localdomain", body.getMemberOf());
		Assert.assertEquals("FirstName", body.getFirstname());
		Assert.assertEquals("LastName", body.getLastname());
		Assert.assertEquals("test-id-123", body.getId());
	}
}
