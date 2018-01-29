package org.venice.beachfront.bfapi.services.proto;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.function.Supplier;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.services.IABrokerService;

import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.LinearRing;
import com.vividsolutions.jts.geom.Polygon;

public class IABrokerServiceProtoImpl implements IABrokerService {
	@Autowired private ExecutorService executorService;

	private int mockActivationDelayMs = 5000;
	private JsonNodeFactory jsonNodeFactory = new JsonNodeFactory(false);
	
	@Override
	public String activateScene(Scene scene, String planetApiKey) {
		try {
			Thread.sleep(this.mockActivationDelayMs);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return scene.getImageMultispectral();
	}

	@Override
	public Scene getScene(String sceneId, String planetApiKey, boolean withTides) {
		GeometryFactory factory = new GeometryFactory();
		Coordinate[] coordArray = new Coordinate[5];
		coordArray[0] = new Coordinate();
		coordArray[1] = new Coordinate(0, 1);
		coordArray[2] = new Coordinate(1, 1);
		coordArray[3] = new Coordinate(1, 0);
		coordArray[3] = new Coordinate();
		return new Scene(
				"source:scene-id-1",
				DateTime.now().minusDays(5),
				0.1,
				factory.createPolygon(coordArray),
				"https://httpbin.org/anything/imageCoastal",
				"https://httpbin.org/anything/imageMultispectral",
				"https://httpbin.org/anything/imageSwir1",
				"platform",
				"resolution",
				"sensor-1",
				"active",
				0.2,
				0.1,
				0.3,
				"/uri/",
				"geotiff");
	}

	@Override
	public CompletableFuture<String> asyncActivateScene(Scene scene, String planetApiKey) {
		IABrokerService this_ = this;
		
		Supplier<String> asyncResponseSupplier = new Supplier<String>(){
			public String get() {
				try {
					return this_.activateScene(scene, planetApiKey);
				} catch (Exception e) {
					throw new RuntimeException(e);
				}

			}
		};

		return CompletableFuture.supplyAsync(asyncResponseSupplier, this.executorService);
	}

}
