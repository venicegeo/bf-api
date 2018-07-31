package org.venice.beachfront.bfapi.model;

import org.joda.time.DateTime;
import org.junit.Test;

import static org.junit.Assert.*;

public class JobTest {

    @Test
    public void testPojo() {
        Job j1 = new Job(
                "job_id",
                "job_name",
                "job_status",
                "created_by_user",
                DateTime.now(),
                "algorithm_id",
                "algorithm_name",
                "algorithm_version",
                "scene_id",
                1.0,
                0.5,
                1.5,
                null,
                false);
        Job j2 = new Job();
        j2.setJobId(j1.getJobId());
        j2.setStatus(j1.getStatus());
        j2.setAlgorithmId(j1.getAlgorithmId());
        j2.setAlgorithmVersion(j1.getAlgorithmVersion());
        j2.setCreatedByUserId(j1.getCreatedByUserId());
        j2.setCreatedOn(j1.getCreatedOn());
        j2.setJobName(j1.getJobName());
        j2.setAlgorithmName(j1.getAlgorithmName());
        j2.setSceneId(j1.getSceneId());
        j2.setTide(j1.getTide());
        j2.setTideMax24h(j1.getTideMax24h());
        j2.setTideMin24h(j1.getTideMin24h());
        j2.setExtras(j1.getExtras());
    }
}