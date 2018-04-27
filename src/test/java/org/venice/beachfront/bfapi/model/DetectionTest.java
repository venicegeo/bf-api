package org.venice.beachfront.bfapi.model;

import org.junit.Assert;
import org.junit.Test;

import static org.junit.Assert.*;

public class DetectionTest {

    @Test
    public void getDetectionPK() {
        Job j1 = new Job();
        j1.setJobId("job_id_1");

        Detection det1 = new Detection(j1, 1, null);
        Detection det2 = new Detection();
        det2.setDetectionPK(det1.getDetectionPK());
        det2.setGeometry(det1.getGeometry());

        Assert.assertEquals(det1.getDetectionPK(), det2.getDetectionPK());
        Assert.assertEquals(det1.getGeometry(), det2.getGeometry());
    }
}