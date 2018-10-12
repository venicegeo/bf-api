package org.venice.beachfront.bfapi.services;

import java.io.File;
import java.io.IOException;

import org.apache.commons.io.IOUtils;
import org.junit.Before;
import org.junit.Test;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.converter.GeoPackageConverter;
import org.venice.beachfront.bfapi.services.converter.ShapefileConverter;

/**
 * Tests data conversion logic
 */
public class ConverterTests {
	private GeoPackageConverter geoPackageConverter = new GeoPackageConverter();
	private ShapefileConverter shapefileConverter = new ShapefileConverter();
	private String emptyGeoJson;

	@Before
	public void setup() throws IOException {
		emptyGeoJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "converter", File.separator, "empty.geojson")),
				"UTF-8");
	}

	@Test
	public void testEmptyGeometryGeoPackageConversion() throws UserException {
		byte[] emptyGeoJsonBytes = emptyGeoJson.getBytes();
		byte[] geoPackageBytes = geoPackageConverter.apply(emptyGeoJsonBytes);
	}

	@Test
	public void testEmptyGeometryShapefileConversion() throws UserException {
		byte[] emptyGeoJsonBytes = emptyGeoJson.getBytes();
		byte[] shapefileBytes = shapefileConverter.apply(emptyGeoJsonBytes);
	}
}
