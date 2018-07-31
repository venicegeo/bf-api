package org.venice.beachfront.bfapi.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Assert;
import org.junit.Test;

import javax.validation.constraints.AssertTrue;
import java.util.HashMap;
import java.util.HashSet;

import static org.junit.Assert.*;

public class DetectionPKTest {

    @Test
    public void testPojo() {
        Job job1 = new Job();
        job1.setJobId("job_1_id");

        Job job2 = new Job();
        job2.setJobId("job_2_id");

        DetectionPK pk3 = new DetectionPK();
        pk3.setJob(job1);
        pk3.setFeatureId(1);

        DetectionPK pk4 = new DetectionPK();
        pk4.setJob(pk3.getJob());
        pk4.setFeatureId(pk3.getFeatureId());

        HashSet<DetectionPK> pkSet = new HashSet<>();

        Assert.assertTrue(pkSet.add(new DetectionPK(job1, 1)));
        Assert.assertTrue(pkSet.add(new DetectionPK(job2, 2)));
        Assert.assertTrue(pkSet.add(new DetectionPK(job1, 3)));
        Assert.assertFalse(pkSet.add(pk3));
        Assert.assertFalse(pkSet.add(pk4));
    }

    @Test
    public void testEquals() {
        DetectionPK pk = new DetectionPK(new Job(), 1);
        Assert.assertFalse(pk.equals(null));
        Assert.assertFalse(pk.equals(new Object()));
        Assert.assertTrue(pk.equals(pk));
    }

}